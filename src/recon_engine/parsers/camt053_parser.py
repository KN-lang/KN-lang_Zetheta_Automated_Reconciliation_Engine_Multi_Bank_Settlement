from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd


class CAMT053ParserError(ValueError):
    """Raised when a CAMT.053 file cannot be parsed safely."""


CAMT053_COLUMNS = [
    "camt053_record_id",
    "account_number",
    "transaction_date",
    "value_date",
    "amount",
    "currency",
    "direction",
    "transaction_reference",
    "account_servicer_reference",
    "counterparty_account",
    "narration",
    "raw_hash",
]


def parse_camt053(path: str | Path) -> pd.DataFrame:
    xml_path = Path(path)
    if not xml_path.exists():
        raise CAMT053ParserError(f"CAMT.053 file not found: {xml_path}")

    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as exc:
        raise CAMT053ParserError(f"Malformed CAMT.053 XML file {xml_path}: {exc}") from exc

    account_number = _text_at(root, ["BkToCstmrStmt", "Stmt", "Acct", "Id", "Othr", "Id"])
    entries = _children(root, "Ntry")
    if not entries:
        raise CAMT053ParserError(f"No Ntry transaction entries found in CAMT.053 file: {xml_path}")

    records = [
        _parse_entry(entry, account_number, sequence_number)
        for sequence_number, entry in enumerate(entries, start=1)
    ]
    return pd.DataFrame(records, columns=CAMT053_COLUMNS)


def _parse_entry(entry: ET.Element, account_number: str, sequence_number: int) -> dict[str, object]:
    amount_node = _child(entry, "Amt")
    if amount_node is None or not (amount_node.text or "").strip():
        raise CAMT053ParserError(f"CAMT.053 Ntry {sequence_number} is missing Amt")

    amount = Decimal(amount_node.text.strip()).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    currency = amount_node.attrib.get("Ccy") or amount_node.attrib.get("CCY") or "UNKNOWN"
    direction = _direction(_text_at(entry, ["CdtDbtInd"]))
    account_servicer_reference = _text_at(entry, ["AcctSvcrRef"])
    end_to_end_id = _text_at(entry, ["NtryDtls", "TxDtls", "Refs", "EndToEndId"])
    record_id = f"CAMT053{sequence_number:06d}"
    transaction_reference = end_to_end_id or account_servicer_reference or record_id
    narration = _text_at(entry, ["NtryDtls", "TxDtls", "RmtInf", "Ustrd"])
    counterparty_account = _counterparty_account(entry, direction)

    raw_payload = ET.tostring(entry, encoding="utf-8")
    return {
        "camt053_record_id": record_id,
        "account_number": account_number or "UNKNOWN",
        "transaction_date": _text_at(entry, ["BookgDt", "Dt"]),
        "value_date": _text_at(entry, ["ValDt", "Dt"]),
        "amount": amount,
        "currency": currency,
        "direction": direction,
        "transaction_reference": transaction_reference,
        "account_servicer_reference": account_servicer_reference,
        "counterparty_account": counterparty_account or "UNKNOWN",
        "narration": narration,
        "raw_hash": hashlib.sha256(raw_payload).hexdigest(),
    }


def _direction(value: str) -> str:
    normalized = value.strip().upper()
    if normalized == "CRDT":
        return "CREDIT"
    if normalized == "DBIT":
        return "DEBIT"
    raise CAMT053ParserError(f"Unsupported CAMT.053 CdtDbtInd value: {value}")


def _counterparty_account(entry: ET.Element, direction: str) -> str:
    if direction == "CREDIT":
        return _text_at(entry, ["NtryDtls", "TxDtls", "RltdPties", "DbtrAcct", "Id", "Othr", "Id"])
    return _text_at(entry, ["NtryDtls", "TxDtls", "RltdPties", "CdtrAcct", "Id", "Othr", "Id"])


def _text_at(element: ET.Element, path: list[str]) -> str:
    current = element
    for tag in path:
        found = _child(current, tag)
        if found is None:
            return ""
        current = found
    return (current.text or "").strip()


def _child(element: ET.Element, local_name: str) -> ET.Element | None:
    for child in list(element):
        if _local_name(child.tag) == local_name:
            return child
    return None


def _children(element: ET.Element, local_name: str) -> list[ET.Element]:
    return [child for child in element.iter() if _local_name(child.tag) == local_name]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]
