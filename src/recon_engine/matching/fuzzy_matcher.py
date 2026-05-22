from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import pandas as pd
from rapidfuzz import fuzz

from recon_engine.matching.match_result import utc_now_iso


MATCH_COLUMNS = [
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


@dataclass(frozen=True)
class FuzzyMatchConfig:
    amount_tolerance: Decimal = Decimal("1.00")
    date_tolerance_days: int = 2
    min_auto_score: Decimal = Decimal("0.85")
    min_review_score: Decimal = Decimal("0.60")


def find_fuzzy_matches(
    internal: pd.DataFrame,
    external: pd.DataFrame,
    matched_internal_ids: set[str],
    matched_external_ids: set[str],
    config: FuzzyMatchConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, set[str], set[str]]:
    """Run a one-to-one fuzzy/tolerance pass over records not matched exactly."""
    internal_candidates = _unmatched_non_duplicates(internal, matched_internal_ids)
    external_candidates = _unmatched_non_duplicates(external, matched_external_ids)

    scored_candidates = [
        _score_candidate(internal_row, external_row, config)
        for _, internal_row in internal_candidates.iterrows()
        for _, external_row in external_candidates.iterrows()
    ]
    scored_candidates.sort(key=lambda candidate: candidate["confidence_score"], reverse=True)

    auto_rows: list[dict[str, object]] = []
    review_rows: list[dict[str, object]] = []
    newly_matched_internal_ids: set[str] = set()
    newly_matched_external_ids: set[str] = set()
    matched_at = utc_now_iso()

    for candidate in scored_candidates:
        internal_id = str(candidate["internal_record_id"])
        external_id = str(candidate["external_record_id"])
        if internal_id in newly_matched_internal_ids or external_id in newly_matched_external_ids:
            continue

        score = Decimal(str(candidate["confidence_score"]))
        if score >= config.min_auto_score:
            auto_rows.append(_matched_row(candidate, matched_at))
            newly_matched_internal_ids.add(internal_id)
            newly_matched_external_ids.add(external_id)
        elif score >= config.min_review_score:
            review_rows.append(candidate)
            newly_matched_internal_ids.add(internal_id)
            newly_matched_external_ids.add(external_id)

    return (
        pd.DataFrame(auto_rows, columns=_matched_columns()),
        pd.DataFrame(review_rows, columns=MATCH_COLUMNS),
        newly_matched_internal_ids,
        newly_matched_external_ids,
    )


def calculate_confidence_score(
    internal_row: pd.Series,
    external_row: pd.Series,
    config: FuzzyMatchConfig,
) -> Decimal:
    text_score = _text_similarity(internal_row, external_row)
    amount_score = _amount_score(internal_row["amount"], external_row["amount"], config.amount_tolerance)
    date_score = _date_score(internal_row["value_date"], external_row["value_date"], config.date_tolerance_days)
    direction_score = Decimal("1") if internal_row["direction"] == external_row["direction"] else Decimal("0")
    currency_score = Decimal("1") if internal_row["currency"] == external_row["currency"] else Decimal("0")

    score = (
        text_score * Decimal("0.40")
        + amount_score * Decimal("0.25")
        + date_score * Decimal("0.15")
        + direction_score * Decimal("0.10")
        + currency_score * Decimal("0.10")
    )
    return score.quantize(Decimal("0.0001"))


def _score_candidate(
    internal_row: pd.Series,
    external_row: pd.Series,
    config: FuzzyMatchConfig,
) -> dict[str, object]:
    score = calculate_confidence_score(internal_row, external_row, config)
    return {
        "internal_record_id": internal_row["record_id"],
        "external_record_id": external_row["record_id"],
        "transaction_reference_internal": internal_row["transaction_reference"],
        "transaction_reference_external": external_row["transaction_reference"],
        "amount_internal": internal_row["amount"],
        "amount_external": external_row["amount"],
        "currency_internal": internal_row["currency"],
        "currency_external": external_row["currency"],
        "direction_internal": internal_row["direction"],
        "direction_external": external_row["direction"],
        "confidence_score": float(score),
        "reason": _reason(internal_row, external_row, config),
    }


def _matched_row(candidate: dict[str, object], matched_at: str) -> dict[str, object]:
    return {
        "internal_record_id": candidate["internal_record_id"],
        "external_record_id": candidate["external_record_id"],
        "transaction_reference": candidate["transaction_reference_internal"],
        "amount": candidate["amount_internal"],
        "currency": candidate["currency_internal"],
        "match_type": _match_type(candidate),
        "confidence_score": candidate["confidence_score"],
        "matched_at": matched_at,
    }


def _match_type(candidate: dict[str, object]) -> str:
    reference_changed = candidate["transaction_reference_internal"] != candidate["transaction_reference_external"]
    amount_changed = candidate["amount_internal"] != candidate["amount_external"]
    if amount_changed:
        return "TOLERANCE"
    if reference_changed:
        return "FUZZY"
    return "TOLERANCE"


def _text_similarity(internal_row: pd.Series, external_row: pd.Series) -> Decimal:
    reference = Decimal(str(fuzz.WRatio(str(internal_row["transaction_reference"]), str(external_row["transaction_reference"])))) / Decimal("100")
    narration = Decimal(str(fuzz.token_set_ratio(str(internal_row["narration"]), str(external_row["narration"])))) / Decimal("100")
    counterparty = Decimal(str(fuzz.WRatio(str(internal_row["counterparty_account"]), str(external_row["counterparty_account"])))) / Decimal("100")
    return (reference * Decimal("0.70") + narration * Decimal("0.20") + counterparty * Decimal("0.10")).quantize(Decimal("0.0001"))


def _amount_score(internal_amount: object, external_amount: object, tolerance: Decimal) -> Decimal:
    difference = abs(Decimal(str(internal_amount)) - Decimal(str(external_amount)))
    if difference == Decimal("0"):
        return Decimal("1")
    if tolerance <= Decimal("0"):
        return Decimal("0")
    return Decimal("1") if difference <= tolerance else Decimal("0")


def _date_score(internal_date: object, external_date: object, tolerance_days: int) -> Decimal:
    delta = abs((pd.to_datetime(internal_date).date() - pd.to_datetime(external_date).date()).days)
    if delta == 0:
        return Decimal("1")
    if tolerance_days <= 0 or delta > tolerance_days:
        return Decimal("0")
    return (Decimal(tolerance_days - delta + 1) / Decimal(tolerance_days + 1)).quantize(Decimal("0.0001"))


def _reason(internal_row: pd.Series, external_row: pd.Series, config: FuzzyMatchConfig) -> str:
    reasons: list[str] = []
    if internal_row["transaction_reference"] != external_row["transaction_reference"]:
        reasons.append("similar reference")
    if internal_row["amount"] != external_row["amount"]:
        difference = abs(Decimal(str(internal_row["amount"])) - Decimal(str(external_row["amount"])))
        tolerance_state = "within" if difference <= config.amount_tolerance else "outside"
        reasons.append(f"amount difference {difference} {tolerance_state} tolerance {config.amount_tolerance}")
    if internal_row["value_date"] != external_row["value_date"]:
        delta = abs((pd.to_datetime(internal_row["value_date"]).date() - pd.to_datetime(external_row["value_date"]).date()).days)
        reasons.append(f"value date difference {delta} days")
    if internal_row["currency"] != external_row["currency"]:
        reasons.append("currency differs")
    if internal_row["direction"] != external_row["direction"]:
        reasons.append("direction differs")
    return "; ".join(reasons) if reasons else "high-confidence fuzzy/tolerance match"


def _unmatched_non_duplicates(frame: pd.DataFrame, matched_ids: set[str]) -> pd.DataFrame:
    duplicate_reference = frame["transaction_reference"].duplicated(keep=False)
    return frame.loc[(~frame["record_id"].isin(matched_ids)) & (~duplicate_reference)].copy()


def _matched_columns() -> list[str]:
    return [
        "internal_record_id",
        "external_record_id",
        "transaction_reference",
        "amount",
        "currency",
        "match_type",
        "confidence_score",
        "matched_at",
    ]
