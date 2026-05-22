from decimal import Decimal

import pandas as pd

from recon_engine.exceptions.classifier import classify_exceptions
from recon_engine.models import ExceptionCategory


def test_exception_classifier_detects_amount_and_missing_records() -> None:
    internal = pd.DataFrame(
        [
            _txn("INTERNAL_LEDGER", "INT1", "UTR1", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
            _txn("INTERNAL_LEDGER", "INT2", "UTR_MISSING_EXT", Decimal("200.00"), "INR", "DEBIT", "2026-05-02"),
        ]
    )
    external = pd.DataFrame(
        [
            _txn("BANK_SETTLEMENT", "BNK1", "UTR1", Decimal("101.00"), "INR", "CREDIT", "2026-05-01"),
            _txn("BANK_SETTLEMENT", "BNK2", "UTR_MISSING_INT", Decimal("300.00"), "INR", "DEBIT", "2026-05-03"),
        ]
    )

    exceptions = classify_exceptions(internal, external, set(), set())
    categories = set(exceptions["exception_category"])

    assert ExceptionCategory.AMOUNT_MISMATCH.value in categories
    assert ExceptionCategory.MISSING_EXTERNAL.value in categories
    assert ExceptionCategory.MISSING_INTERNAL.value in categories


def test_exception_classifier_detects_duplicates() -> None:
    internal = pd.DataFrame(
        [
            _txn("INTERNAL_LEDGER", "INT1", "UTR_DUP", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
            _txn("INTERNAL_LEDGER", "INT2", "UTR_DUP", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
        ]
    )
    external = pd.DataFrame(
        [
            _txn("BANK_SETTLEMENT", "BNK1", "UTR_EXT_DUP", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
            _txn("BANK_SETTLEMENT", "BNK2", "UTR_EXT_DUP", Decimal("100.00"), "INR", "CREDIT", "2026-05-01"),
        ]
    )

    exceptions = classify_exceptions(internal, external, set(), set())
    categories = set(exceptions["exception_category"])

    assert ExceptionCategory.DUPLICATE_INTERNAL.value in categories
    assert ExceptionCategory.DUPLICATE_EXTERNAL.value in categories


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
