from decimal import Decimal

import pandas as pd

from recon_engine.matching.exact_matcher import find_exact_matches
from recon_engine.models import CANONICAL_COLUMNS
from recon_engine.normalisation.normalizer import normalize_camt053_statement, normalize_internal_ledger
from recon_engine.parsers.camt053_parser import parse_camt053


def test_camt053_parser_extracts_transactions(tmp_path) -> None:
    path = tmp_path / "statement.xml"
    path.write_text(_sample_camt053(), encoding="utf-8")

    parsed = parse_camt053(path)

    assert len(parsed) == 2
    assert parsed.loc[0, "account_number"] == "ACCT1001"
    assert parsed.loc[0, "transaction_reference"] == "TXN123"
    assert parsed.loc[0, "narration"] == "UPI payment reference TXN123"
    assert parsed.loc[0, "counterparty_account"] == "DBTR123"


def test_camt053_amount_and_currency_parsing(tmp_path) -> None:
    path = tmp_path / "statement.xml"
    path.write_text(_sample_camt053(), encoding="utf-8")

    parsed = parse_camt053(path)

    assert parsed.loc[0, "amount"] == Decimal("25.00")
    assert parsed.loc[0, "currency"] == "INR"


def test_camt053_direction_mapping_credit_and_debit(tmp_path) -> None:
    path = tmp_path / "statement.xml"
    path.write_text(_sample_camt053(), encoding="utf-8")

    parsed = parse_camt053(path)

    assert parsed.loc[0, "direction"] == "CREDIT"
    assert parsed.loc[1, "direction"] == "DEBIT"


def test_camt053_end_to_end_id_fallback_to_account_servicer_reference(tmp_path) -> None:
    path = tmp_path / "statement.xml"
    path.write_text(_sample_camt053_without_end_to_end_id(), encoding="utf-8")

    parsed = parse_camt053(path)

    assert parsed.loc[0, "transaction_reference"] == "SERVICER-REF-1"


def test_camt053_normalization_outputs_canonical_schema(tmp_path) -> None:
    path = tmp_path / "statement.xml"
    path.write_text(_sample_camt053(), encoding="utf-8")

    normalized = normalize_camt053_statement(parse_camt053(path))

    assert list(normalized.columns) == CANONICAL_COLUMNS
    assert normalized.loc[0, "source_system"] == "CAMT053"
    assert normalized.loc[0, "status"] == "SUCCESS"
    assert normalized.loc[0, "payment_rail"] == "UPI"


def test_camt053_reconciliation_components_end_to_end(tmp_path) -> None:
    internal = pd.DataFrame(
        [
            {
                "internal_txn_id": "INT1",
                "utr": "TXN123",
                "account_number": "ACCT1001",
                "counterparty_account": "DBTR123",
                "txn_date": "2026-05-22",
                "value_date": "2026-05-22",
                "amount": "25.00",
                "currency": "INR",
                "debit_credit": "CREDIT",
                "rail": "UPI",
                "narration": "UPI payment reference TXN123",
                "status": "SUCCESS",
            }
        ]
    )
    path = tmp_path / "statement.xml"
    path.write_text(_sample_camt053(), encoding="utf-8")

    matched, _, _ = find_exact_matches(
        normalize_internal_ledger(internal),
        normalize_camt053_statement(parse_camt053(path)),
    )

    assert len(matched) == 1


def _sample_camt053() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
  <BkToCstmrStmt>
    <Stmt>
      <Acct><Id><Othr><Id>ACCT1001</Id></Othr></Id></Acct>
      <Ntry>
        <Amt Ccy="INR">25.00</Amt>
        <CdtDbtInd>CRDT</CdtDbtInd>
        <BookgDt><Dt>2026-05-22</Dt></BookgDt>
        <ValDt><Dt>2026-05-22</Dt></ValDt>
        <AcctSvcrRef>SERVICER-REF-1</AcctSvcrRef>
        <NtryDtls><TxDtls>
          <Refs><EndToEndId>TXN123</EndToEndId></Refs>
          <RltdPties>
            <CdtrAcct><Id><Othr><Id>CDTR123</Id></Othr></Id></CdtrAcct>
            <DbtrAcct><Id><Othr><Id>DBTR123</Id></Othr></Id></DbtrAcct>
          </RltdPties>
          <RmtInf><Ustrd>UPI payment reference TXN123</Ustrd></RmtInf>
        </TxDtls></NtryDtls>
      </Ntry>
      <Ntry>
        <Amt Ccy="INR">10.50</Amt>
        <CdtDbtInd>DBIT</CdtDbtInd>
        <BookgDt><Dt>2026-05-23</Dt></BookgDt>
        <ValDt><Dt>2026-05-23</Dt></ValDt>
        <AcctSvcrRef>SERVICER-REF-2</AcctSvcrRef>
        <NtryDtls><TxDtls>
          <Refs><EndToEndId>TXN124</EndToEndId></Refs>
          <RltdPties>
            <CdtrAcct><Id><Othr><Id>CDTR124</Id></Othr></Id></CdtrAcct>
            <DbtrAcct><Id><Othr><Id>DBTR124</Id></Othr></Id></DbtrAcct>
          </RltdPties>
          <RmtInf><Ustrd>Card settlement TXN124</Ustrd></RmtInf>
        </TxDtls></NtryDtls>
      </Ntry>
    </Stmt>
  </BkToCstmrStmt>
</Document>
"""


def _sample_camt053_without_end_to_end_id() -> str:
    return """<Document>
  <BkToCstmrStmt><Stmt>
    <Acct><Id><Othr><Id>ACCT1001</Id></Othr></Id></Acct>
    <Ntry>
      <Amt Ccy="INR">25.00</Amt>
      <CdtDbtInd>CRDT</CdtDbtInd>
      <BookgDt><Dt>2026-05-22</Dt></BookgDt>
      <ValDt><Dt>2026-05-22</Dt></ValDt>
      <AcctSvcrRef>SERVICER-REF-1</AcctSvcrRef>
      <NtryDtls><TxDtls><Refs><EndToEndId></EndToEndId></Refs></TxDtls></NtryDtls>
    </Ntry>
  </Stmt></BkToCstmrStmt>
</Document>
"""
