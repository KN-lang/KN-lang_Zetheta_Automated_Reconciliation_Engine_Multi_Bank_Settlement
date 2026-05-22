from decimal import Decimal

import pandas as pd

from recon_engine.matching.fuzzy_matcher import FuzzyMatchConfig, calculate_confidence_score, find_fuzzy_matches


def test_fuzzy_reference_similarity_auto_matches_near_reference() -> None:
    internal = pd.DataFrame([_txn("INTERNAL_LEDGER", "INT1", "UTR-ABC-001", Decimal("100.00"), "2026-05-01")])
    external = pd.DataFrame([_txn("BANK_SETTLEMENT", "BNK1", "UTRABC001", Decimal("100.00"), "2026-05-01")])

    matches, review_queue, internal_ids, external_ids = find_fuzzy_matches(internal, external, set(), set(), FuzzyMatchConfig())

    assert len(matches) == 1
    assert matches.loc[0, "match_type"] == "FUZZY"
    assert review_queue.empty
    assert internal_ids == {"INT1"}
    assert external_ids == {"BNK1"}


def test_amount_tolerance_can_auto_match_small_difference() -> None:
    internal = pd.DataFrame([_txn("INTERNAL_LEDGER", "INT1", "UTR1", Decimal("100.00"), "2026-05-01")])
    external = pd.DataFrame([_txn("BANK_SETTLEMENT", "BNK1", "UTR1", Decimal("100.50"), "2026-05-01")])

    matches, _, _, _ = find_fuzzy_matches(
        internal,
        external,
        set(),
        set(),
        FuzzyMatchConfig(amount_tolerance=Decimal("1.00")),
    )

    assert len(matches) == 1
    assert matches.loc[0, "match_type"] == "TOLERANCE"


def test_date_tolerance_contributes_to_confidence_score() -> None:
    internal = pd.Series(_txn("INTERNAL_LEDGER", "INT1", "UTR1", Decimal("100.00"), "2026-05-01"))
    external = pd.Series(_txn("BANK_SETTLEMENT", "BNK1", "UTR1", Decimal("100.00"), "2026-05-03"))

    score = calculate_confidence_score(internal, external, FuzzyMatchConfig(date_tolerance_days=2))

    assert score >= Decimal("0.85")


def test_confidence_scoring_sends_medium_score_to_review_queue() -> None:
    internal = pd.DataFrame(
        [
            _txn(
                "INTERNAL_LEDGER",
                "INT1",
                "ABC999",
                Decimal("100.00"),
                "2026-05-01",
                narration="Acme services invoice",
            )
        ]
    )
    external = pd.DataFrame(
        [
            _txn(
                "BANK_SETTLEMENT",
                "BNK1",
                "XYZ999",
                Decimal("102.50"),
                "2026-05-01",
                narration="Acme services invoice",
            )
        ]
    )

    matches, review_queue, internal_ids, external_ids = find_fuzzy_matches(
        internal,
        external,
        set(),
        set(),
        FuzzyMatchConfig(amount_tolerance=Decimal("1.00"), min_auto_score=Decimal("0.85"), min_review_score=Decimal("0.60")),
    )

    assert matches.empty
    assert len(review_queue) == 1
    assert review_queue.loc[0, "internal_record_id"] == "INT1"
    assert internal_ids == {"INT1"}
    assert external_ids == {"BNK1"}


def _txn(
    source: str,
    record_id: str,
    ref: str,
    amount: Decimal,
    value_date: str,
    narration: str = "Payment to Acme",
) -> dict[str, object]:
    return {
        "source_system": source,
        "record_id": record_id,
        "transaction_reference": ref,
        "account_number": "A1",
        "counterparty_account": "CP1",
        "transaction_date": value_date,
        "value_date": value_date,
        "amount": amount,
        "currency": "INR",
        "direction": "CREDIT",
        "payment_rail": "UPI",
        "narration": narration,
        "status": "SUCCESS",
        "raw_hash": record_id,
    }
