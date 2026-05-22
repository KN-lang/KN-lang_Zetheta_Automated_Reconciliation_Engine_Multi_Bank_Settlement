from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from recon_engine.config import DEFAULT_EXTERNAL_FILE, DEFAULT_GENERATED_DIR, DEFAULT_INTERNAL_FILE, DEFAULT_OUTPUT_DIR
from recon_engine.exceptions.classifier import classify_exceptions
from recon_engine.matching.exact_matcher import find_exact_matches
from recon_engine.normalisation.normalizer import (
    BANK_REQUIRED_COLUMNS,
    INTERNAL_REQUIRED_COLUMNS,
    normalize_bank_settlement,
    normalize_internal_ledger,
)
from recon_engine.parsers.csv_parser import read_csv
from recon_engine.reports.report_writer import AuditLog, write_reports
from recon_engine.simulation.sample_data_generator import generate_sample_data as generate_data

app = typer.Typer(help="Automated reconciliation engine for multi-bank settlement systems.")
console = Console()


@app.command("generate-sample-data")
def generate_sample_data(
    output: Path = typer.Option(DEFAULT_GENERATED_DIR, "--output", "-o", help="Directory for generated CSV files."),
    count: int = typer.Option(100, "--count", "-c", min=20, help="Approximate number of sample transactions."),
) -> None:
    internal_path, bank_path = generate_data(output, count)
    console.print(f"Generated internal ledger: {internal_path}")
    console.print(f"Generated bank settlement: {bank_path}")


@app.command("reconcile")
def reconcile(
    internal: Path = typer.Option(DEFAULT_INTERNAL_FILE, "--internal", help="Internal ledger CSV path."),
    external: Path = typer.Option(DEFAULT_EXTERNAL_FILE, "--external", help="Bank settlement CSV path."),
    output: Path = typer.Option(DEFAULT_OUTPUT_DIR, "--output", "-o", help="Output directory for reports."),
) -> None:
    audit = AuditLog()

    internal_raw = read_csv(internal, INTERNAL_REQUIRED_COLUMNS)
    audit.add("LOAD_INTERNAL", f"Loaded {internal}", len(internal_raw))

    external_raw = read_csv(external, BANK_REQUIRED_COLUMNS)
    audit.add("LOAD_EXTERNAL", f"Loaded {external}", len(external_raw))

    internal_normalized = normalize_internal_ledger(internal_raw)
    external_normalized = normalize_bank_settlement(external_raw)
    audit.add("NORMALIZE_INTERNAL", "Normalized internal ledger to canonical schema", len(internal_normalized))
    audit.add("NORMALIZE_EXTERNAL", "Normalized bank settlement to canonical schema", len(external_normalized))

    matched, matched_internal_ids, matched_external_ids = find_exact_matches(internal_normalized, external_normalized)
    audit.add("MATCH_EXACT", "Applied exact matching on reference, amount, currency, direction, and value date", len(matched))

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
    )
    console.print(f"Wrote reports to: {output}")
    console.print(f"Matched records: {summary['matched_count']}")
    console.print(f"Exceptions: {summary['exception_count']}")
    console.print(f"Match rate: {summary['match_rate_percent']}%")


def main() -> None:
    app()
