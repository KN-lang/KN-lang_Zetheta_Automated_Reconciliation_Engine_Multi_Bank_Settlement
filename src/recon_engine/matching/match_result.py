from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class MatchRecord:
    internal_record_id: str
    external_record_id: str
    transaction_reference: str
    amount: Decimal
    currency: str
    match_type: str
    confidence_score: float
    matched_at: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
