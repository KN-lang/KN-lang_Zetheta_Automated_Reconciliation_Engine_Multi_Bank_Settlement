from __future__ import annotations

import hashlib
import re
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd


class MT940ParserError(ValueError):
    """Raised when an MT940 statement cannot be parsed safely."""


MT940_COLUMNS = [
    "mt940_record_id",
    "account_number",
    "transaction_date",
    "value_date",
    "amount",
    "currency",
    "direction",
    "transaction_reference",
    "bank_reference",
    "transaction_type",
    "narration",
    "raw_hash",
]

STATEMENT_LINE_PATTERN = re.compile(
    r"^:61:"
    r"(?P<value_date>\d{6})"
    r"(?P<entry_date>\d{4})?"
    r"(?P<direction>[CD])"
    r"(?P<amount>\d+(?:,\d{1,2})?)"
    r"N(?P<transaction_type>[A-Z0-9]{3})"
    r"(?P<customer_reference>[^/]*)"
    r"(?://(?P<bank_reference>.*))?$"
)


def parse_mt940(path: str | Path) -> pd.DataFrame:
    mt940_path = Path(path)
    if not mt940_path.exists():
        raise MT940ParserError(f"MT940 file not found: {mt940_path}")

    lines = mt940_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise MT940ParserError(f"MT940 file is empty: {mt940_path}")

    account_number = ""
    currency = ""
    records: list[dict[str, object]] = []
    current_record: dict[str, object] | None = None

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(":25:"):
            account_number = line.removeprefix(":25:").strip()
            continue
        if line.startswith(":60F:") or line.startswith(":62F:"):
            currency = _currency_from_balance_tag(line) or currency
            continue
        if line.startswith(":61:"):
            if not account_number:
                raise MT940ParserError("MT940 statement line encountered before :25: account tag")
            if current_record is not None:
                records.append(current_record)
            current_record = _parse_statement_line(line, account_number, currency, len(records) + 1)
            continue
        if line.startswith(":86:"):
            if current_record is None:
                raise MT940ParserError(":86: narration encountered before a :61: statement line")
            current_record["narration"] = line.removeprefix(":86:").strip()
            continue

    if current_record is not None:
        records.append(current_record)
    if not records:
        raise MT940ParserError(f"No :61: statement lines found in MT940 file: {mt940_path}")

    return pd.DataFrame(records, columns=MT940_COLUMNS)


def _parse_statement_line(
    line: str,
    account_number: str,
    currency: str,
    sequence_number: int,
) -> dict[str, object]:
    match = STATEMENT_LINE_PATTERN.match(line)
    if not match:
        raise MT940ParserError(f"Malformed MT940 :61: statement line: {line}")

    value_date = _parse_yymmdd(match.group("value_date"))
    entry_date = _parse_entry_date(match.group("entry_date"), value_date)
    amount = Decimal(match.group("amount").replace(",", ".")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    customer_reference = match.group("customer_reference").strip()
    bank_reference = (match.group("bank_reference") or "").strip()
    transaction_reference = customer_reference if customer_reference and customer_reference != "NONREF" else bank_reference
    if not transaction_reference:
        transaction_reference = f"MT940-{sequence_number:06d}"

    raw_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
    return {
        "mt940_record_id": f"MT940{sequence_number:06d}",
        "account_number": account_number,
        "transaction_date": entry_date.isoformat(),
        "value_date": value_date.isoformat(),
        "amount": amount,
        "currency": currency or "UNKNOWN",
        "direction": "CREDIT" if match.group("direction") == "C" else "DEBIT",
        "transaction_reference": transaction_reference,
        "bank_reference": bank_reference,
        "transaction_type": match.group("transaction_type"),
        "narration": "",
        "raw_hash": raw_hash,
    }


def _parse_yymmdd(value: str) -> date:
    year = 2000 + int(value[:2])
    month = int(value[2:4])
    day = int(value[4:6])
    return date(year, month, day)


def _parse_entry_date(value: str | None, value_date: date) -> date:
    if not value:
        return value_date
    month = int(value[:2])
    day = int(value[2:4])
    return date(value_date.year, month, day)


def _currency_from_balance_tag(line: str) -> str:
    match = re.match(r"^:6[02]F:[CD]\d{6}(?P<currency>[A-Z]{3})", line)
    return match.group("currency") if match else ""
