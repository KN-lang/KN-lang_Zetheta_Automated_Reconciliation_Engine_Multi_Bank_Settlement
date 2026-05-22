from decimal import Decimal

import pandas as pd

from recon_engine.reports.report_writer import build_summary


def test_summary_generation_basic_sanity() -> None:
    exceptions = pd.DataFrame(
        [
            {"exception_category": "MISSING_INTERNAL"},
            {"exception_category": "MISSING_INTERNAL"},
            {"exception_category": "AMOUNT_MISMATCH"},
        ]
    )

    summary = build_summary(
        total_internal_records=10,
        total_external_records=11,
        matched_count=7,
        exceptions=exceptions,
    )

    assert summary["matched_count"] == 7
    assert summary["exception_count"] == 3
    assert summary["match_rate_percent"] == Decimal("70.00") or summary["match_rate_percent"] == 70.0
    assert summary["exception_breakdown"]["MISSING_INTERNAL"] == 2
