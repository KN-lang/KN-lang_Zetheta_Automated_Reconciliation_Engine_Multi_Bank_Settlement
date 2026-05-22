from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from time import perf_counter

import pandas as pd

from recon_engine.exceptions.classifier import classify_exceptions
from recon_engine.matching.exact_matcher import find_exact_matches
from recon_engine.matching.fuzzy_matcher import FuzzyMatchConfig, find_fuzzy_matches
from recon_engine.normalisation.normalizer import (
    BANK_REQUIRED_COLUMNS,
    INTERNAL_REQUIRED_COLUMNS,
    normalize_bank_settlement,
    normalize_camt053_statement,
    normalize_internal_ledger,
    normalize_mt940_statement,
)
from recon_engine.parsers.camt053_parser import parse_camt053
from recon_engine.parsers.csv_parser import read_csv
from recon_engine.parsers.mt940_parser import parse_mt940
from recon_engine.reports.report_writer import AuditLog, write_reports
from recon_engine.simulation.sample_data_generator import generate_sample_data


def run_benchmark(records: int = 1000) -> dict[str, object]:
    generated_dir = Path("data/generated")
    output_dir = Path("data/output")
    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []

    start = perf_counter()
    paths = generate_sample_data(generated_dir, records, include_mt940=True, include_camt053=True)
    duration = perf_counter() - start
    results.append(
        _benchmark_row(
            benchmark_name="sample_generation",
            format_tested="csv+mt940+camt053",
            records_processed=records,
            duration_seconds=duration,
        )
    )

    internal_path = paths[0]
    scenarios = [
        ("csv_fuzzy", "csv", paths[1]),
        ("mt940_fuzzy", "mt940", _path_by_suffix(paths, ".mt940")),
        ("camt053_fuzzy", "camt053", _path_by_suffix(paths, ".xml")),
    ]

    for benchmark_name, external_format, external_path in scenarios:
        start = perf_counter()
        summary = _run_reconciliation(internal_path, external_path, external_format, output_dir)
        duration = perf_counter() - start
        results.append(
            _benchmark_row(
                benchmark_name=benchmark_name,
                format_tested=external_format,
                records_processed=int(summary["total_internal_records"]) + int(summary["total_external_records"]),
                duration_seconds=duration,
                matched_count=int(summary["matched_count"]),
                review_required_count=int(summary["review_required_count"]),
                exception_count=int(summary["exception_count"]),
            )
        )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "requested_records": records,
        "results": results,
    }
    (output_dir / "benchmark_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (reports_dir / "benchmark_results.md").write_text(_benchmark_markdown(payload), encoding="utf-8")
    return payload


def _run_reconciliation(
    internal_path: Path,
    external_path: Path,
    external_format: str,
    output_dir: Path,
) -> dict[str, object]:
    internal_raw = read_csv(internal_path, INTERNAL_REQUIRED_COLUMNS)
    internal_normalized = normalize_internal_ledger(internal_raw)
    external_raw, external_normalized, parser_used = _load_external(external_path, external_format)

    matched, matched_internal_ids, matched_external_ids = find_exact_matches(internal_normalized, external_normalized)
    fuzzy_matches, review_queue, fuzzy_internal_ids, fuzzy_external_ids = find_fuzzy_matches(
        internal_normalized,
        external_normalized,
        matched_internal_ids,
        matched_external_ids,
        FuzzyMatchConfig(
            amount_tolerance=Decimal("1.00"),
            date_tolerance_days=2,
            min_auto_score=Decimal("0.85"),
            min_review_score=Decimal("0.60"),
        ),
    )
    if not fuzzy_matches.empty:
        matched = pd.concat([matched, fuzzy_matches], ignore_index=True)

    matched_internal_ids = matched_internal_ids | fuzzy_internal_ids | set(
        review_queue["internal_record_id"].tolist() if not review_queue.empty else []
    )
    matched_external_ids = matched_external_ids | fuzzy_external_ids | set(
        review_queue["external_record_id"].tolist() if not review_queue.empty else []
    )
    exceptions = classify_exceptions(
        internal_normalized,
        external_normalized,
        matched_internal_ids,
        matched_external_ids,
    )

    audit = AuditLog()
    audit.add("BENCHMARK_LOAD_INTERNAL", f"Loaded {internal_path}", len(internal_raw))
    audit.add("BENCHMARK_LOAD_EXTERNAL", f"Loaded {external_path} as {external_format}", len(external_raw))
    audit.add("BENCHMARK_MATCH", "Ran exact and fuzzy matching", len(matched))
    audit.add("BENCHMARK_EXCEPTIONS", "Classified benchmark exceptions", len(exceptions))

    return write_reports(
        output_dir,
        matched,
        exceptions,
        audit,
        total_internal_records=len(internal_normalized),
        total_external_records=len(external_normalized),
        review_queue=review_queue,
        metadata={"external_format": external_format, "parser_used": parser_used},
    )


def _load_external(path: Path, external_format: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if external_format == "csv":
        raw = read_csv(path, BANK_REQUIRED_COLUMNS)
        return raw, normalize_bank_settlement(raw), "csv_parser"
    if external_format == "mt940":
        raw = parse_mt940(path)
        return raw, normalize_mt940_statement(raw), "mt940_parser"
    if external_format == "camt053":
        raw = parse_camt053(path)
        return raw, normalize_camt053_statement(raw), "camt053_parser"
    raise ValueError(f"Unsupported benchmark external format: {external_format}")


def _path_by_suffix(paths: tuple[Path, ...], suffix: str) -> Path:
    for path in paths:
        if path.suffix == suffix:
            return path
    raise ValueError(f"Generated path with suffix {suffix} was not found")


def _benchmark_row(
    benchmark_name: str,
    format_tested: str,
    records_processed: int,
    duration_seconds: float,
    matched_count: int | None = None,
    review_required_count: int | None = None,
    exception_count: int | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "benchmark_name": benchmark_name,
        "format_tested": format_tested,
        "records_processed": records_processed,
        "duration_seconds": round(duration_seconds, 4),
        "records_per_second": round(records_processed / duration_seconds, 2) if duration_seconds > 0 else 0,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if matched_count is not None:
        row["matched_count"] = matched_count
    if review_required_count is not None:
        row["review_required_count"] = review_required_count
    if exception_count is not None:
        row["exception_count"] = exception_count
    return row


def _benchmark_markdown(payload: dict[str, object]) -> str:
    rows = payload["results"]
    lines = [
        "# Benchmark Results",
        "",
        f"- Generated at: `{payload['generated_at']}`",
        f"- Requested records: `{payload['requested_records']}`",
        "",
        "| Benchmark | Format | Records | Seconds | Records/sec | Matched | Review | Exceptions |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {benchmark_name} | {format_tested} | {records_processed} | {duration_seconds} | "
            "{records_per_second} | {matched_count} | {review_required_count} | {exception_count} |".format(
                benchmark_name=row["benchmark_name"],
                format_tested=row["format_tested"],
                records_processed=row["records_processed"],
                duration_seconds=row["duration_seconds"],
                records_per_second=row["records_per_second"],
                matched_count=row.get("matched_count", ""),
                review_required_count=row.get("review_required_count", ""),
                exception_count=row.get("exception_count", ""),
            )
        )
    lines.append("")
    lines.append("These results are laptop-scale smoke benchmarks, not production capacity claims.")
    return "\n".join(lines)
