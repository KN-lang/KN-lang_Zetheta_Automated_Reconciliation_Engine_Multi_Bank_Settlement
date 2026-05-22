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
) -> dict[str, object]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    matched.to_csv(target / "matched.csv", index=False)
    exceptions.to_csv(target / "exceptions.csv", index=False)
    audit_log.to_frame().to_csv(target / "audit_log.csv", index=False)

    summary = build_summary(total_internal_records, total_external_records, len(matched), exceptions)
    (target / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def build_summary(
    total_internal_records: int,
    total_external_records: int,
    matched_count: int,
    exceptions: pd.DataFrame,
) -> dict[str, object]:
    exception_breakdown = (
        exceptions["exception_category"].value_counts().sort_index().to_dict() if not exceptions.empty else {}
    )
    denominator = max(total_internal_records, 1)
    return {
        "total_internal_records": total_internal_records,
        "total_external_records": total_external_records,
        "matched_count": matched_count,
        "exception_count": int(len(exceptions)),
        "match_rate_percent": round((matched_count / denominator) * 100, 2),
        "exception_breakdown": exception_breakdown,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
