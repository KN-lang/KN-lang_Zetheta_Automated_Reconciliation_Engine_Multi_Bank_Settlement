from __future__ import annotations

import pandas as pd

from recon_engine.models import ExceptionCategory


def classify_exceptions(
    internal: pd.DataFrame,
    external: pd.DataFrame,
    matched_internal_ids: set[str],
    matched_external_ids: set[str],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    duplicate_internal_ids = set(internal.loc[internal["transaction_reference"].duplicated(keep=False), "record_id"])
    duplicate_external_ids = set(external.loc[external["transaction_reference"].duplicated(keep=False), "record_id"])
    rows.extend(_duplicate_rows(internal, "INTERNAL", ExceptionCategory.DUPLICATE_INTERNAL))
    rows.extend(_duplicate_rows(external, "EXTERNAL", ExceptionCategory.DUPLICATE_EXTERNAL))

    internal_excluded_ids = matched_internal_ids | duplicate_internal_ids
    external_excluded_ids = matched_external_ids | duplicate_external_ids
    internal_unmatched = internal[~internal["record_id"].isin(internal_excluded_ids)]
    external_unmatched = external[~external["record_id"].isin(external_excluded_ids)]
    internal_by_ref = {row["transaction_reference"]: row for _, row in internal.iterrows()}
    external_by_ref = {row["transaction_reference"]: row for _, row in external.iterrows()}

    for _, row in internal_unmatched.iterrows():
        ref = row["transaction_reference"]
        external_row = external_by_ref.get(ref)
        if external_row is None:
            rows.append(_exception(row, "INTERNAL", ExceptionCategory.MISSING_EXTERNAL, "No external record with same transaction reference"))
            continue
        category, reason = _compare(row, external_row, ExceptionCategory.UNMATCHED_INTERNAL)
        rows.append(_exception(row, "INTERNAL", category, reason, related_record_id=external_row["record_id"]))

    for _, row in external_unmatched.iterrows():
        ref = row["transaction_reference"]
        internal_row = internal_by_ref.get(ref)
        if internal_row is None:
            rows.append(_exception(row, "EXTERNAL", ExceptionCategory.MISSING_INTERNAL, "No internal record with same transaction reference"))
            continue
        category, reason = _compare(internal_row, row, ExceptionCategory.UNMATCHED_EXTERNAL)
        rows.append(_exception(row, "EXTERNAL", category, reason, related_record_id=internal_row["record_id"]))

    return pd.DataFrame(
        rows,
        columns=[
            "source_side",
            "record_id",
            "related_record_id",
            "transaction_reference",
            "exception_category",
            "amount",
            "currency",
            "direction",
            "value_date",
            "reason",
        ],
    ).drop_duplicates()


def _duplicate_rows(frame: pd.DataFrame, side: str, category: ExceptionCategory) -> list[dict[str, object]]:
    duplicates = frame[frame["transaction_reference"].duplicated(keep=False)]
    return [
        _exception(row, side, category, "Duplicate transaction reference in same source")
        for _, row in duplicates.iterrows()
    ]


def _compare(
    internal_row: pd.Series,
    external_row: pd.Series,
    default_category: ExceptionCategory,
) -> tuple[ExceptionCategory, str]:
    # Fuzzy reference matching and amount tolerances are planned for Phase 2.
    if internal_row["amount"] != external_row["amount"]:
        return ExceptionCategory.AMOUNT_MISMATCH, "Same reference but amount differs"
    if internal_row["currency"] != external_row["currency"]:
        return ExceptionCategory.CURRENCY_MISMATCH, "Same reference but currency differs"
    if internal_row["direction"] != external_row["direction"]:
        return ExceptionCategory.DIRECTION_MISMATCH, "Same reference but direction differs"
    if internal_row["value_date"] != external_row["value_date"]:
        return ExceptionCategory.DATE_MISMATCH, "Same reference but value date differs"
    return default_category, "Record did not satisfy exact match criteria"


def _exception(
    row: pd.Series,
    side: str,
    category: ExceptionCategory,
    reason: str,
    related_record_id: str = "",
) -> dict[str, object]:
    return {
        "source_side": side,
        "record_id": row["record_id"],
        "related_record_id": related_record_id,
        "transaction_reference": row["transaction_reference"],
        "exception_category": category.value,
        "amount": row["amount"],
        "currency": row["currency"],
        "direction": row["direction"],
        "value_date": row["value_date"],
        "reason": reason,
    }
