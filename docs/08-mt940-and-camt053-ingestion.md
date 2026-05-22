# MT940 and CAMT.053 Ingestion

The engine now supports CSV and a practical MT940 parser. CAMT.053 remains planned for Phase 4.

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

## CAMT.053 (ISO 20022) Ingestion (Planned)
- **Format:** XML.
- **Strategy:**
    - Use `lxml` for XPath-based extraction of `<Ntry>` (Entry) nodes.
    - Map `<Amt>` (Amount), `<ValDt>` (Value Date), and `<AcctSvcrRef>` (Account Servicer Reference) to the Canonical Model.
    - Support for multi-currency statements within a single file.

## Integration Plan
1. **Current CLI Selection:** `--external-format csv|mt940`.
2. **Unified Normalization:** Regardless of input, the matching engine only sees canonical transaction rows.
3. **Future Parser Selection:** Consider a parser registry or factory when CAMT.053 is added.
