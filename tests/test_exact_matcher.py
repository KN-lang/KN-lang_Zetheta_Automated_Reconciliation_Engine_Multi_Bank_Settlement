from decimal import Decimal

import pandas as pd

from recon_engine.matching.exact_matcher import find_exact_matches


def test_exact_matcher_matches_reference_amount_currency_direction_and_date() -> None:
    internal = pd.DataFrame(
        [
            _txn("INTERNAL_LEDGER", "INT1", "UTR1", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
            _txn("INTERNAL_LEDGER", "INT2", "UTR2", Decimal("200.00"), "INR", "DEBIT", "2026-05-02"),
        ]
    )
    external = pd.DataFrame(
        [
            _txn("BANK_SETTLEMENT", "BNK1", "UTR1", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
            _txn("BANK_SETTLEMENT", "BNK2", "UTR2", Decimal("201.00"), "INR", "DEBIT", "2026-05-02"),
        ]
    )

    matched, matched_internal_ids, matched_external_ids = find_exact_matches(internal, external)

    assert len(matched) == 1
    assert matched.loc[0, "internal_record_id"] == "INT1"
    assert matched.loc[0, "external_record_id"] == "BNK1"
    assert matched.loc[0, "match_type"] == "EXACT"
    assert matched.loc[0, "confidence_score"] == 1.0
    assert matched_internal_ids == {"INT1"}
    assert matched_external_ids == {"BNK1"}


def _txn(source: str, record_id: str, ref: str, amount: Decimal, currency: str, direction: str, value_date: str) -> dict[str, object]:
    return {
        "source_system": source,
        "record_id": record_id,
        "transaction_reference": ref,
        "account_number": "A1",
        "counterparty_account": "C1",
        "transaction_date": value_date,
        "value_date": value_date,
        "amount": amount,
        "currency": currency,
        "direction": direction,
        "payment_rail": "UPI",
        "narration": "test",
        "status": "SUCCESS",
        "raw_hash": record_id,
    }
