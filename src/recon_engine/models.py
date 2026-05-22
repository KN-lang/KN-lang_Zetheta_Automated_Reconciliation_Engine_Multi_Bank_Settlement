from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Direction(StrEnum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class PaymentRail(StrEnum):
    UPI = "UPI"
    NEFT = "NEFT"
    RTGS = "RTGS"
    IMPS = "IMPS"
    CARD = "CARD"
    UNKNOWN = "UNKNOWN"


class TransactionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    REVERSED = "REVERSED"
    UNKNOWN = "UNKNOWN"


class ExceptionCategory(StrEnum):
    MISSING_INTERNAL = "MISSING_INTERNAL"
    MISSING_EXTERNAL = "MISSING_EXTERNAL"
    AMOUNT_MISMATCH = "AMOUNT_MISMATCH"
    DATE_MISMATCH = "DATE_MISMATCH"
    CURRENCY_MISMATCH = "CURRENCY_MISMATCH"
    DIRECTION_MISMATCH = "DIRECTION_MISMATCH"
    DUPLICATE_INTERNAL = "DUPLICATE_INTERNAL"
    DUPLICATE_EXTERNAL = "DUPLICATE_EXTERNAL"
    UNMATCHED_INTERNAL = "UNMATCHED_INTERNAL"
    UNMATCHED_EXTERNAL = "UNMATCHED_EXTERNAL"


class CanonicalTransaction(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    source_system: str
    record_id: str
    transaction_reference: str
    account_number: str
    counterparty_account: str
    transaction_date: date
    value_date: date
    amount: Decimal = Field(decimal_places=2)
    currency: str
    direction: Direction
    payment_rail: PaymentRail
    narration: str
    status: TransactionStatus
    raw_hash: str


CANONICAL_COLUMNS = [
    "source_system",
    "record_id",
    "transaction_reference",
    "account_number",
    "counterparty_account",
    "transaction_date",
    "value_date",
    "amount",
    "currency",
    "direction",
    "payment_rail",
    "narration",
    "status",
    "raw_hash",
]
