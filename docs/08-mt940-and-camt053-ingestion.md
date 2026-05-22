# MT940 and CAMT.053 Ingestion

The engine now supports CSV, a practical MT940 parser, and a practical CAMT.053 parser.

## MT940 (SWIFT) Ingestion (Implemented)
- **Format:** Tag-based flat file.
- **Strategy:** 
    - Use a regex-based parser to extract `:61:` statement lines and `:86:` narration.
    - Extract account number from `:25:`.
    - Extract statement currency from `:60F:` or `:62F:`.
    - Convert comma-decimal MT940 amounts into `Decimal`.
    - Map `C` to `CREDIT` and `D` to `DEBIT`.
    - Use the customer reference from `:61:`; fallback to bank reference or generated record id when missing.
    - Normalize parsed rows into the canonical transaction schema with `source_system = MT940`.

### Supported Simulated Statement Line Shape

```text
:61:YYMMDDMMDDC123,45NTRFNONREF//BANKREF123
:61:YYMMDDMMDDD123,45NTRFREF123//BANKREF456
```

This is not a full global SWIFT parser. It is intentionally scoped to project simulation and common statement-line structure.

## CAMT.053 (ISO 20022) Ingestion (Implemented)
- **Format:** XML.
- **Strategy:**
    - Use Python `ElementTree` with namespace-tolerant local-name matching.
    - Extract `<Ntry>` transaction entries.
    - Map `<Amt Ccy="">`, `<CdtDbtInd>`, `<BookgDt>`, `<ValDt>`, `<AcctSvcrRef>`, `<EndToEndId>`, related party account, and `<RmtInf><Ustrd>` into parser rows.
    - Prefer `<EndToEndId>` as transaction reference, fallback to `<AcctSvcrRef>`, then generated record id.
    - Convert XML amounts into `Decimal`.
    - Map `CRDT` to `CREDIT` and `DBIT` to `DEBIT`.
    - Normalize parsed rows into the canonical transaction schema with `source_system = CAMT053`.

This parser is practical and namespace-tolerant for simulated/common CAMT.053 records. It is not a full ISO 20022 certification engine.

## Integration Plan
1. **Current CLI Selection:** `--external-format csv|mt940|camt053`.
2. **Unified Normalization:** Regardless of input, the matching engine only sees canonical transaction rows.
3. **Future Parser Selection:** Consider a parser registry or factory if more external formats are added.
