from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd


def generate_sample_data(output_dir: str | Path = "data/generated", count: int = 100) -> tuple[Path, Path]:
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
    return internal_path, bank_path


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
