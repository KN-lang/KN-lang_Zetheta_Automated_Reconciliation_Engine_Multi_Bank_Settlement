from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


class AuditLog:
    def __init__(self) -> None:
        self._rows: list[dict[str, object]] = []

    def add(self, stage: str, message: str, record_count: int, status: str = "SUCCESS") -> None:
        self._rows.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "stage": stage,
                "message": message,
                "record_count": record_count,
                "status": status,
            }
        )

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(self._rows, columns=["timestamp", "stage", "message", "record_count", "status"])


def write_reports(
    output_dir: str | Path,
    matched: pd.DataFrame,
    exceptions: pd.DataFrame,
    audit_log: AuditLog,
    total_internal_records: int,
    total_external_records: int,
    review_queue: pd.DataFrame | None = None,
) -> dict[str, object]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    review_queue = _normalize_review_queue(review_queue)
    summary = build_summary(total_internal_records, total_external_records, matched, exceptions, review_queue)

    matched.to_csv(target / "matched.csv", index=False)
    exceptions.to_csv(target / "exceptions.csv", index=False)
    review_queue.to_csv(target / "review_queue.csv", index=False)
    audit_log.to_frame().to_csv(target / "audit_log.csv", index=False)
    (target / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_excel_report(target / "reconciliation_report.xlsx", summary, matched, exceptions, review_queue, audit_log.to_frame())
    return summary


def build_summary(
    total_internal_records: int,
    total_external_records: int,
    matched: int | pd.DataFrame | None = None,
    exceptions: pd.DataFrame | None = None,
    review_queue: pd.DataFrame | None = None,
    matched_count: int | None = None,
) -> dict[str, object]:
    if matched is None:
        matched = matched_count if matched_count is not None else 0
    exceptions = exceptions if exceptions is not None else pd.DataFrame(columns=["exception_category"])
    matched_frame = _coerce_matched_frame(matched)
    review_queue = _normalize_review_queue(review_queue)
    exception_breakdown = (
        exceptions["exception_category"].value_counts().sort_index().to_dict() if not exceptions.empty else {}
    )
    denominator = max(total_internal_records, 1)
    matched_count = len(matched_frame)
    exact_match_count = _match_type_count(matched_frame, "EXACT")
    fuzzy_match_count = _match_type_count(matched_frame, "FUZZY")
    tolerance_match_count = _match_type_count(matched_frame, "TOLERANCE")
    review_required_count = len(review_queue)
    unmatched_count = int(len(exceptions))
    return {
        "total_internal_records": total_internal_records,
        "total_external_records": total_external_records,
        "matched_count": matched_count,
        "exact_match_count": exact_match_count,
        "fuzzy_match_count": fuzzy_match_count,
        "tolerance_match_count": tolerance_match_count,
        "review_required_count": review_required_count,
        "auto_match_count": matched_count,
        "unmatched_count": unmatched_count,
        "exception_count": int(len(exceptions)),
        "match_rate_percent": round((matched_count / denominator) * 100, 2),
        "review_rate_percent": round((review_required_count / denominator) * 100, 2),
        "exception_breakdown": exception_breakdown,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def write_excel_report(
    path: str | Path,
    summary: dict[str, object],
    matched: pd.DataFrame,
    exceptions: pd.DataFrame,
    review_queue: pd.DataFrame,
    audit_log: pd.DataFrame,
) -> None:
    summary_frame = pd.DataFrame([{"metric": key, "value": json.dumps(value) if isinstance(value, dict) else value} for key, value in summary.items()])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_frame.to_excel(writer, sheet_name="Summary", index=False)
        matched.to_excel(writer, sheet_name="Matched", index=False)
        exceptions.to_excel(writer, sheet_name="Exceptions", index=False)
        review_queue.to_excel(writer, sheet_name="Review Queue", index=False)
        audit_log.to_excel(writer, sheet_name="Audit Log", index=False)


def _match_type_count(matched: pd.DataFrame, match_type: str) -> int:
    if matched.empty or "match_type" not in matched.columns:
        return 0
    return int((matched["match_type"] == match_type).sum())


def _coerce_matched_frame(matched: int | pd.DataFrame) -> pd.DataFrame:
    if isinstance(matched, pd.DataFrame):
        return matched
    return pd.DataFrame([{"match_type": "UNKNOWN"} for _ in range(matched)])


def _empty_review_queue() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "internal_record_id",
            "external_record_id",
            "transaction_reference_internal",
            "transaction_reference_external",
            "amount_internal",
            "amount_external",
            "currency_internal",
            "currency_external",
            "direction_internal",
            "direction_external",
            "confidence_score",
            "reason",
        ]
    )


def _normalize_review_queue(review_queue: pd.DataFrame | None) -> pd.DataFrame:
    if review_queue is None or (review_queue.empty and len(review_queue.columns) == 0):
        return _empty_review_queue()
    return review_queue
