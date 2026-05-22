from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

from recon_engine.config import DEFAULT_EXTERNAL_FILE, DEFAULT_GENERATED_DIR, DEFAULT_INTERNAL_FILE, DEFAULT_OUTPUT_DIR
from recon_engine.exceptions.classifier import classify_exceptions
from recon_engine.matching.exact_matcher import find_exact_matches
from recon_engine.matching.fuzzy_matcher import FuzzyMatchConfig, find_fuzzy_matches
from recon_engine.normalisation.normalizer import (
    BANK_REQUIRED_COLUMNS,
    INTERNAL_REQUIRED_COLUMNS,
    normalize_camt053_statement,
    normalize_mt940_statement,
    normalize_bank_settlement,
    normalize_internal_ledger,
)
from recon_engine.parsers.csv_parser import read_csv
from recon_engine.parsers.camt053_parser import parse_camt053
from recon_engine.parsers.mt940_parser import parse_mt940
from recon_engine.reports.report_writer import AuditLog, write_reports
from recon_engine.simulation.sample_data_generator import generate_sample_data as generate_data

app = typer.Typer(help="Automated reconciliation engine for multi-bank settlement systems.")
console = Console()


@app.command("generate-sample-data")
def generate_sample_data(
    output: Path = typer.Option(DEFAULT_GENERATED_DIR, "--output", "-o", help="Directory for generated CSV files."),
    count: int = typer.Option(100, "--count", "-c", min=20, help="Approximate number of sample transactions."),
    include_mt940: bool = typer.Option(False, "--include-mt940", help="Also generate a simulated MT940 statement."),
    include_camt053: bool = typer.Option(False, "--include-camt053", help="Also generate a simulated CAMT.053 statement."),
) -> None:
    paths = generate_data(output, count, include_mt940=include_mt940, include_camt053=include_camt053)
    internal_path, bank_path = paths[0], paths[1]
    console.print(f"Generated internal ledger: {internal_path}")
    console.print(f"Generated bank settlement: {bank_path}")
    for path in paths[2:]:
        if path.suffix == ".mt940":
            console.print(f"Generated MT940 statement: {path}")
        elif path.suffix == ".xml":
            console.print(f"Generated CAMT.053 statement: {path}")


@app.command("reconcile")
def reconcile(
    internal: Path = typer.Option(DEFAULT_INTERNAL_FILE, "--internal", help="Internal ledger CSV path."),
    external: Path = typer.Option(DEFAULT_EXTERNAL_FILE, "--external", help="Bank settlement CSV path."),
    external_format: str = typer.Option("csv", "--external-format", help="External input format: csv, mt940, or camt053."),
    output: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output", "-o", help="Output directory for reports."),
    enable_fuzzy: bool = typer.Option(False, "--enable-fuzzy", help="Enable fuzzy and tolerance-based matching."),
    amount_tolerance: str = typer.Option("1.00", "--amount-tolerance", help="Absolute amount tolerance."),
    date_tolerance_days: int = typer.Option(2, "--date-tolerance-days", min=0, help="Allowed value-date tolerance in days."),
    min_auto_score: str = typer.Option("0.85", "--min-auto-score", help="Minimum score for automatic fuzzy/tolerance match."),
    min_review_score: str = typer.Option("0.60", "--min-review-score", help="Minimum score for review queue."),
) -> None:
    audit = AuditLog()

    internal_raw = read_csv(internal, INTERNAL_REQUIRED_COLUMNS)
    audit.add("LOAD_INTERNAL", f"Loaded {internal}", len(internal_raw))

    normalized_external_format = external_format.lower()
    if normalized_external_format == "csv":
        external_raw = read_csv(external, BANK_REQUIRED_COLUMNS)
        external_normalized = normalize_bank_settlement(external_raw)
        parser_used = "csv_parser"
    elif normalized_external_format == "mt940":
        external_raw = parse_mt940(external)
        external_normalized = normalize_mt940_statement(external_raw)
        parser_used = "mt940_parser"
    elif normalized_external_format == "camt053":
        external_raw = parse_camt053(external)
        external_normalized = normalize_camt053_statement(external_raw)
        parser_used = "camt053_parser"
    else:
        raise typer.BadParameter("external_format must be csv, mt940, or camt053")
    audit.add("LOAD_EXTERNAL", f"Loaded {external} as {normalized_external_format}", len(external_raw))

    internal_normalized = normalize_internal_ledger(internal_raw)
    audit.add("NORMALIZE_INTERNAL", "Normalized internal ledger to canonical schema", len(internal_normalized))
    audit.add("NORMALIZE_EXTERNAL", f"Normalized {normalized_external_format} records to canonical schema", len(external_normalized))

    matched, matched_internal_ids, matched_external_ids = find_exact_matches(internal_normalized, external_normalized)
    audit.add("MATCH_EXACT", "Applied exact matching on reference, amount, currency, direction, and value date", len(matched))

    review_queue = pd.DataFrame()
    if enable_fuzzy:
        config = FuzzyMatchConfig(
            amount_tolerance=_decimal_option(amount_tolerance, "amount_tolerance"),
            date_tolerance_days=date_tolerance_days,
            min_auto_score=_decimal_option(min_auto_score, "min_auto_score"),
            min_review_score=_decimal_option(min_review_score, "min_review_score"),
        )
        fuzzy_matches, review_queue, fuzzy_internal_ids, fuzzy_external_ids = find_fuzzy_matches(
            internal_normalized,
            external_normalized,
            matched_internal_ids,
            matched_external_ids,
            config,
        )
        if not fuzzy_matches.empty:
            matched = pd.concat([matched, fuzzy_matches], ignore_index=True)
        matched_internal_ids = matched_internal_ids | fuzzy_internal_ids | set(review_queue["internal_record_id"].tolist() if not review_queue.empty else [])
        matched_external_ids = matched_external_ids | fuzzy_external_ids | set(review_queue["external_record_id"].tolist() if not review_queue.empty else [])
        audit.add(
            "MATCH_FUZZY",
            "Applied fuzzy and tolerance matching with weighted confidence scoring",
            len(fuzzy_matches),
        )
        audit.add("REVIEW_QUEUE", "Generated review queue for medium-confidence candidates", len(review_queue))

    exceptions = classify_exceptions(
        internal_normalized,
        external_normalized,
        matched_internal_ids,
        matched_external_ids,
    )
    audit.add("CLASSIFY_EXCEPTIONS", "Classified unmatched and problematic records", len(exceptions))

    summary = write_reports(
        output,
        matched,
        exceptions,
        audit,
        total_internal_records=len(internal_normalized),
        total_external_records=len(external_normalized),
        review_queue=review_queue,
        metadata={"external_format": normalized_external_format, "parser_used": parser_used},
    )
    console.print(f"Wrote reports to: {output}")
    console.print(f"Matched records: {summary['matched_count']}")
    console.print(f"Review required: {summary['review_required_count']}")
    console.print(f"Exceptions: {summary['exception_count']}")
    console.print(f"Match rate: {summary['match_rate_percent']}%")


def main() -> None:
    app()


def _decimal_option(value: str, name: str) -> Decimal:
    try:
        return Decimal(value)
    except Exception as exc:
        raise typer.BadParameter(f"{name} must be a decimal value") from exc
