from decimal import Decimal

import pandas as pd

from recon_engine.models import CANONICAL_COLUMNS
from recon_engine.normalisation.normalizer import normalize_internal_ledger, normalize_mt940_statement
from recon_engine.parsers.mt940_parser import parse_mt940


def test_mt940_parser_extracts_expected_transactions(tmp_path) -> None:
    path = tmp_path / "statement.mt940"
    path.write_text(_sample_mt940(), encoding="utf-8")

    parsed = parse_mt940(path)

    assert len(parsed) == 2
    assert parsed.loc[0, "account_number"] == "ACCT1001"
    assert parsed.loc[0, "transaction_reference"] == "REF123"
    assert parsed.loc[0, "narration"] == "Invoice payment REF123"
    assert parsed.loc[1, "transaction_reference"] == "BANKREF456"


def test_mt940_amount_conversion_with_comma_decimal(tmp_path) -> None:
    path = tmp_path / "statement.mt940"
    path.write_text(_sample_mt940(), encoding="utf-8")

    parsed = parse_mt940(path)

    assert parsed.loc[0, "amount"] == Decimal("123.45")


def test_mt940_direction_mapping_credit_and_debit(tmp_path) -> None:
    path = tmp_path / "statement.mt940"
    path.write_text(_sample_mt940(), encoding="utf-8")

    parsed = parse_mt940(path)

    assert parsed.loc[0, "direction"] == "CREDIT"
    assert parsed.loc[1, "direction"] == "DEBIT"


def test_mt940_normalization_outputs_canonical_schema(tmp_path) -> None:
    path = tmp_path / "statement.mt940"
    path.write_text(_sample_mt940(), encoding="utf-8")
    parsed = parse_mt940(path)

    normalized = normalize_mt940_statement(parsed)

    assert list(normalized.columns) == CANONICAL_COLUMNS
    assert normalized.loc[0, "source_system"] == "MT940"
    assert normalized.loc[0, "status"] == "SUCCESS"
    assert normalized.loc[0, "counterparty_account"] == "UNKNOWN"


def test_mt940_reconciliation_components_end_to_end(tmp_path) -> None:
    internal = pd.DataFrame(
        [
            {
                "internal_txn_id": "INT1",
                "utr": "REF123",
                "account_number": "ACCT1001",
                "counterparty_account": "UNKNOWN",
                "txn_date": "2026-05-01",
                "value_date": "2026-05-01",
                "amount": "123.45",
                "currency": "INR",
                "debit_credit": "CREDIT",
                "rail": "NEFT",
                "narration": "Invoice payment REF123",
                "status": "SUCCESS",
            }
        ]
    )
    path = tmp_path / "statement.mt940"
    path.write_text(_sample_mt940(), encoding="utf-8")

    internal_normalized = normalize_internal_ledger(internal)
    external_normalized = normalize_mt940_statement(parse_mt940(path))

    from recon_engine.matching.exact_matcher import find_exact_matches

    matched, _, _ = find_exact_matches(internal_normalized, external_normalized)
    assert len(matched) == 1


def _sample_mt940() -> str:
    return "\n".join(
        [
            "{1:F01SIMULATEDBANK0000000000}{2:I940RECONENGINE}{4:",
            ":20:TESTREF",
            ":25:ACCT1001",
            ":28C:00001/001",
            ":60F:C260501INR0,00",
            ":61:2605010501C123,45NTRFREF123//BANKREF123",
            ":86:Invoice payment REF123",
            ":61:2605020502D67,89NTRFNONREF//BANKREF456",
            ":86:Debit with missing customer reference",
            ":62F:C260531INR55,56",
            "-}",
        ]
    )
