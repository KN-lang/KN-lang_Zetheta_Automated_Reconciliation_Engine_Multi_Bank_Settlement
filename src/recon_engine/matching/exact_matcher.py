from __future__ import annotations

from decimal import Decimal

import pandas as pd

from recon_engine.matching.match_result import utc_now_iso

MATCH_COLUMNS = ["transaction_reference", "amount", "currency", "direction"]


def find_exact_matches(internal: pd.DataFrame, external: pd.DataFrame) -> tuple[pd.DataFrame, set[str], set[str]]:
    """Return one-to-one exact matches, ignoring duplicate references for exception handling."""
    internal_unique = _non_duplicate_candidates(internal)
    external_unique = _non_duplicate_candidates(external)

    merged = internal_unique.merge(
        external_unique,
        on=MATCH_COLUMNS,
        suffixes=("_internal", "_external"),
        how="inner",
    )

    matched_at = utc_now_iso()
    rows = [
        {
            "internal_record_id": row["record_id_internal"],
            "external_record_id": row["record_id_external"],
            "transaction_reference": row["transaction_reference"],
            "amount": _money(row["amount"]),
            "currency": row["currency"],
            "match_type": "EXACT",
            "confidence_score": 1.0,
            "matched_at": matched_at,
        }
        for _, row in merged.iterrows()
        if row["value_date_internal"] == row["value_date_external"]
    ]

    matched = pd.DataFrame(
        rows,
        columns=[
            "internal_record_id",
            "external_record_id",
            "transaction_reference",
            "amount",
            "currency",
            "match_type",
            "confidence_score",
            "matched_at",
        ],
    )
    return (
        matched,
        set(matched["internal_record_id"].tolist()) if not matched.empty else set(),
        set(matched["external_record_id"].tolist()) if not matched.empty else set(),
    )


def _non_duplicate_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    duplicate_reference = frame["transaction_reference"].duplicated(keep=False)
    return frame.loc[~duplicate_reference].copy()


def _money(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))
