from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET

import pandas as pd


def generate_sample_data(
    output_dir: str | Path = "data/generated",
    count: int = 100,
    include_mt940: bool = False,
    include_camt053: bool = False,
) -> tuple[Path, ...]:
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    internal_rows: list[dict[str, object]] = []
    bank_rows: list[dict[str, object]] = []
    base_date = date(2026, 5, 1)
    rails = ["UPI", "NEFT", "RTGS", "IMPS", "CARD"]

    for index in range(count):
        ref = f"UTR{index:06d}"
        amount = Decimal("1000.00") + Decimal(index * 7)
        direction = "CREDIT" if index % 2 == 0 else "DEBIT"
        txn_date = base_date + timedelta(days=index % 20)
        rail = rails[index % len(rails)]
        currency = "INR"

        internal_rows.append(
            {
                "internal_txn_id": f"INT{index:06d}",
                "utr": ref,
                "account_number": "ACCT1001",
                "counterparty_account": f"CP{index:06d}",
                "txn_date": txn_date.isoformat(),
                "value_date": txn_date.isoformat(),
                "amount": f"{amount:.2f}",
                "currency": currency,
                "debit_credit": direction,
                "rail": rail,
                "narration": f"Internal payment {index}",
                "status": "SUCCESS",
            }
        )

        bank_rows.append(
            {
                "bank_txn_id": f"BNK{index:06d}",
                "bank_reference": ref,
                "account_no": "ACCT1001",
                "counterparty": f"CP{index:06d}",
                "posted_date": txn_date.isoformat(),
                "value_date": txn_date.isoformat(),
                "transaction_amount": f"{amount:.2f}",
                "currency_code": currency,
                "cr_dr": "CR" if direction == "CREDIT" else "DR",
                "payment_type": rail,
                "description": f"Bank settlement {index}",
                "settlement_status": "SUCCESS",
            }
        )

    _apply_exception_scenarios(internal_rows, bank_rows, base_date)

    internal_path = target / "internal_ledger.csv"
    bank_path = target / "bank_settlement.csv"
    pd.DataFrame(internal_rows).to_csv(internal_path, index=False)
    pd.DataFrame(bank_rows).to_csv(bank_path, index=False)
    paths: list[Path] = [internal_path, bank_path]
    if include_mt940 or include_camt053:
        mt940_path = target / "bank_statement.mt940"
        mt940_path.write_text(_build_mt940_statement(bank_rows), encoding="utf-8")
        paths.append(mt940_path)
    if include_camt053:
        camt053_path = target / "bank_statement_camt053.xml"
        ET.ElementTree(_build_camt053_document(bank_rows)).write(camt053_path, encoding="utf-8", xml_declaration=True)
        paths.append(camt053_path)
    return tuple(paths)


def _apply_exception_scenarios(
    internal_rows: list[dict[str, object]],
    bank_rows: list[dict[str, object]],
    base_date: date,
) -> None:
    bank_rows[5]["bank_reference"] = "UTR-000005"  # fuzzy reference scenario
    bank_rows.pop(10)  # missing external
    internal_rows.pop(20)  # missing internal
    bank_rows[30]["transaction_amount"] = "9999.99"
    bank_rows[40]["value_date"] = (base_date + timedelta(days=9)).isoformat()
    internal_rows[50]["currency"] = "USD"
    bank_rows[60]["cr_dr"] = "DR" if bank_rows[60]["cr_dr"] == "CR" else "CR"

    duplicate_external = dict(bank_rows[70])
    duplicate_external["bank_txn_id"] = "BNK_DUP_EXT_000070"
    duplicate_external["description"] = "Duplicate external settlement"
    bank_rows.append(duplicate_external)

    duplicate_internal = dict(internal_rows[80])
    duplicate_internal["internal_txn_id"] = "INT_DUP_INT_000080"
    duplicate_internal["narration"] = "Duplicate internal ledger"
    internal_rows.append(duplicate_internal)


def _build_mt940_statement(bank_rows: list[dict[str, object]]) -> str:
    statement_rows = [dict(row) for row in bank_rows[:35]]
    statement_rows[6]["transaction_amount"] = "7777.77"  # amount mismatch
    statement_rows[7]["value_date"] = "2026-05-20"  # date mismatch
    statement_rows[8]["bank_reference"] = "UTR-000008"  # narration/reference variation

    missing_internal = dict(statement_rows[0])
    missing_internal["bank_txn_id"] = "MT940_MISSING_INTERNAL"
    missing_internal["bank_reference"] = "UTR_MT940_ONLY"
    missing_internal["transaction_amount"] = "4321.00"
    missing_internal["description"] = "MT940 only settlement"
    statement_rows.append(missing_internal)

    duplicate_reference = dict(statement_rows[12])
    duplicate_reference["bank_txn_id"] = "MT940_DUPLICATE_000012"
    duplicate_reference["description"] = "MT940 duplicate settlement"
    statement_rows.append(duplicate_reference)

    lines = [
        "{1:F01SIMULATEDBANK0000000000}{2:I940RECONENGINE}{4:",
        ":20:SIMMT940202605",
        ":25:ACCT1001",
        ":28C:00001/001",
        ":60F:C260501INR0,00",
    ]
    for row in statement_rows:
        lines.append(_mt940_statement_line(row))
        lines.append(f":86:{row['description']}")
    lines.extend([":62F:C260531INR999999,99", "-}"])
    return "\n".join(lines) + "\n"


def _mt940_statement_line(row: dict[str, object]) -> str:
    value_date = date.fromisoformat(str(row["value_date"]))
    posted_date = date.fromisoformat(str(row["posted_date"]))
    direction = "C" if str(row["cr_dr"]).upper() == "CR" else "D"
    amount = str(row["transaction_amount"]).replace(".", ",")
    transaction_type = _mt940_transaction_type(str(row["payment_type"]))
    reference = str(row["bank_reference"])
    return (
        f":61:{value_date:%y%m%d}{posted_date:%m%d}"
        f"{direction}{amount}N{transaction_type}{reference}//{row['bank_txn_id']}"
    )


def _mt940_transaction_type(payment_type: str) -> str:
    return {
        "RTGS": "RTG",
        "UPI": "UPI",
        "NEFT": "TRF",
        "IMPS": "TRF",
        "CARD": "MSC",
    }.get(payment_type.upper(), "TRF")


def _build_camt053_document(bank_rows: list[dict[str, object]]) -> ET.Element:
    statement_rows = [dict(row) for row in bank_rows[:35]]
    statement_rows[6]["transaction_amount"] = "7777.77"  # amount mismatch
    statement_rows[7]["value_date"] = "2026-05-20"  # date mismatch
    statement_rows[8]["bank_reference"] = "UTR-000008"  # narration/reference variation

    missing_internal = dict(statement_rows[0])
    missing_internal["bank_txn_id"] = "CAMT_MISSING_INTERNAL"
    missing_internal["bank_reference"] = "UTR_CAMT_ONLY"
    missing_internal["transaction_amount"] = "5432.10"
    missing_internal["description"] = "CAMT only settlement"
    statement_rows.append(missing_internal)

    duplicate_reference = dict(statement_rows[12])
    duplicate_reference["bank_txn_id"] = "CAMT_DUPLICATE_000012"
    duplicate_reference["description"] = "CAMT duplicate settlement"
    statement_rows.append(duplicate_reference)

    document = ET.Element("Document")
    bank_to_customer = ET.SubElement(document, "BkToCstmrStmt")
    statement = ET.SubElement(bank_to_customer, "Stmt")
    account = ET.SubElement(statement, "Acct")
    account_id = ET.SubElement(ET.SubElement(ET.SubElement(account, "Id"), "Othr"), "Id")
    account_id.text = "ACCT1001"

    for row in statement_rows:
        _append_camt053_entry(statement, row)
    return document


def _append_camt053_entry(statement: ET.Element, row: dict[str, object]) -> None:
    entry = ET.SubElement(statement, "Ntry")
    amount = ET.SubElement(entry, "Amt", {"Ccy": str(row["currency_code"])})
    amount.text = str(row["transaction_amount"])
    direction = ET.SubElement(entry, "CdtDbtInd")
    direction.text = "CRDT" if str(row["cr_dr"]).upper() == "CR" else "DBIT"
    booking_date = ET.SubElement(ET.SubElement(entry, "BookgDt"), "Dt")
    booking_date.text = str(row["posted_date"])
    value_date = ET.SubElement(ET.SubElement(entry, "ValDt"), "Dt")
    value_date.text = str(row["value_date"])
    servicer_ref = ET.SubElement(entry, "AcctSvcrRef")
    servicer_ref.text = str(row["bank_txn_id"])

    tx_details = ET.SubElement(ET.SubElement(entry, "NtryDtls"), "TxDtls")
    end_to_end_id = ET.SubElement(ET.SubElement(tx_details, "Refs"), "EndToEndId")
    end_to_end_id.text = str(row["bank_reference"])

    related_parties = ET.SubElement(tx_details, "RltdPties")
    creditor = ET.SubElement(related_parties, "CdtrAcct")
    ET.SubElement(ET.SubElement(ET.SubElement(creditor, "Id"), "Othr"), "Id").text = str(row["counterparty"])
    debtor = ET.SubElement(related_parties, "DbtrAcct")
    ET.SubElement(ET.SubElement(ET.SubElement(debtor, "Id"), "Othr"), "Id").text = str(row["counterparty"])

    remittance = ET.SubElement(ET.SubElement(tx_details, "RmtInf"), "Ustrd")
    remittance.text = f"{row['payment_type']} {row['description']}"
