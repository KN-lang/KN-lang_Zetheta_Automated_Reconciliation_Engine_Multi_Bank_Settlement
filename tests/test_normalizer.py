from decimal import Decimal

import pandas as pd

from recon_engine.models import CANONICAL_COLUMNS
from recon_engine.normalisation.normalizer import normalize_bank_settlement, normalize_internal_ledger


def test_internal_normalizer_outputs_canonical_schema() -> None:
    raw = pd.DataFrame(
        [
            {
                "internal_txn_id": "INT1",
                "utr": "UTR1",
                "account_number": "A1",
                "counterparty_account": "C1",
                "txn_date": "2026-05-01",
                "value_date": "2026-05-01",
                "amount": "100.005",
                "currency": "inr",
                "debit_credit": "cr",
                "rail": "upi",
                "narration": "test",
                "status": "success",
            }
        ]
    )

    normalized = normalize_internal_ledger(raw)

    assert list(normalized.columns) == CANONICAL_COLUMNS
    assert normalized.loc[0, "amount"] == Decimal("100.01")
    assert normalized.loc[0, "direction"] == "CREDIT"
    assert normalized.loc[0, "payment_rail"] == "UPI"
    assert normalized.loc[0, "status"] == "SUCCESS"
    assert len(normalized.loc[0, "raw_hash"]) == 64


def test_bank_normalizer_outputs_canonical_schema() -> None:
    raw = pd.DataFrame(
        [
            {
                "bank_txn_id": "BNK1",
                "bank_reference": "UTR1",
                "account_no": "A1",
                "counterparty": "C1",
                "posted_date": "2026-05-01",
                "value_date": "2026-05-01",
                "transaction_amount": "100.00",
                "currency_code": "INR",
                "cr_dr": "DR",
                "payment_type": "NEFT",
                "description": "test",
                "settlement_status": "SUCCESS",
            }
        ]
    )

    normalized = normalize_bank_settlement(raw)

    assert list(normalized.columns) == CANONICAL_COLUMNS
    assert normalized.loc[0, "record_id"] == "BNK1"
    assert normalized.loc[0, "direction"] == "DEBIT"
