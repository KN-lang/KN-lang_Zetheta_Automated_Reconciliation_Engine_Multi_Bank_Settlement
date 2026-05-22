from __future__ import annotations

import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

from recon_engine.models import CANONICAL_COLUMNS

INTERNAL_REQUIRED_COLUMNS = [
    "internal_txn_id",
    "utr",
    "account_number",
    "counterparty_account",
    "txn_date",
    "value_date",
    "amount",
    "currency",
    "debit_credit",
    "rail",
    "narration",
    "status",
]

BANK_REQUIRED_COLUMNS = [
    "bank_txn_id",
    "bank_reference",
    "account_no",
    "counterparty",
    "posted_date",
    "value_date",
    "transaction_amount",
    "currency_code",
    "cr_dr",
    "payment_type",
    "description",
    "settlement_status",
]


def normalize_internal_ledger(frame: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "source_system": "INTERNAL_LEDGER",
            "record_id": row["internal_txn_id"],
            "transaction_reference": row["utr"],
            "account_number": row["account_number"],
            "counterparty_account": row["counterparty_account"],
            "transaction_date": _date(row["txn_date"]),
            "value_date": _date(row["value_date"]),
            "amount": _money(row["amount"]),
            "currency": _upper(row["currency"]),
            "direction": _direction(row["debit_credit"]),
            "payment_rail": _rail(row["rail"]),
            "narration": row["narration"],
            "status": _status(row["status"]),
            "raw_hash": _raw_hash(row.to_dict()),
        }
        for _, row in frame.iterrows()
    ]
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def normalize_bank_settlement(frame: pd.DataFrame) -> pd.DataFrame:
    rows = [
        {
            "source_system": "BANK_SETTLEMENT",
            "record_id": row["bank_txn_id"],
            "transaction_reference": row["bank_reference"],
            "account_number": row["account_no"],
            "counterparty_account": row["counterparty"],
            "transaction_date": _date(row["posted_date"]),
            "value_date": _date(row["value_date"]),
            "amount": _money(row["transaction_amount"]),
            "currency": _upper(row["currency_code"]),
            "direction": _direction(row["cr_dr"]),
            "payment_rail": _rail(row["payment_type"]),
            "narration": row["description"],
            "status": _status(row["settlement_status"]),
            "raw_hash": _raw_hash(row.to_dict()),
        }
        for _, row in frame.iterrows()
    ]
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def _money(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _date(value: object) -> str:
    return pd.to_datetime(value).date().isoformat()


def _upper(value: object) -> str:
    return str(value).strip().upper()


def _direction(value: object) -> str:
    normalized = _upper(value)
    if normalized in {"CR", "C", "CREDIT"}:
        return "CREDIT"
    if normalized in {"DR", "D", "DEBIT"}:
        return "DEBIT"
    raise ValueError(f"Unsupported direction value: {value}")


def _rail(value: object) -> str:
    normalized = _upper(value)
    return normalized if normalized in {"UPI", "NEFT", "RTGS", "IMPS", "CARD"} else "UNKNOWN"


def _status(value: object) -> str:
    normalized = _upper(value)
    return normalized if normalized in {"SUCCESS", "FAILED", "PENDING", "REVERSED"} else "UNKNOWN"


def _raw_hash(row: dict[str, object]) -> str:
    payload = json.dumps(row, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
