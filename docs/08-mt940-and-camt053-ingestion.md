# MT940 and CAMT.053 Ingestion (Roadmap)

While Phase 1 focuses on CSV, the architecture is designed to support standard banking formats.

## MT940 (SWIFT) Ingestion
- **Format:** Tag-based flat file.
- **Strategy:** 
    - Use a regex-based parser to extract Tag 61 (Transaction) and Tag 86 (Details).
    - Map Tag 61 amount and date to the Canonical Model.
    - Extract the reference from Tag 86 using bank-specific patterns.

## CAMT.053 (ISO 20022) Ingestion
- **Format:** XML.
- **Strategy:**
    - Use `lxml` for XPath-based extraction of `<Ntry>` (Entry) nodes.
    - Map `<Amt>` (Amount), `<ValDt>` (Value Date), and `<AcctSvcrRef>` (Account Servicer Reference) to the Canonical Model.
    - Support for multi-currency statements within a single file.

## Integration Plan
1. **Abstract Parser Class:** Define a common interface `BaseParser`.
2. **Factory Pattern:** Instantiate the correct parser based on file extension or header content.
3. **Unified Normalization:** Regardless of input, the matching engine only sees `CanonicalTransaction` objects.
