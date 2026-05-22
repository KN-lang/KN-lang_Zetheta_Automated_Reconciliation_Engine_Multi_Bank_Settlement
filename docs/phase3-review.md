# Phase 3 Review: MT940 Parser Implementation

## 1. MT940 Parser Design
The MT940 parser in `src/recon_engine/parsers/mt940_parser.py` uses a regex-based approach for tag extraction, specifically targeting `:61:` (Statement Line) and `:86:` (Information to Account Owner). 
- **Strengths:** It correctly handles MT940-specific conventions like comma decimals and YYMMDD dates. The state machine approach for `:25:`, `:60F:`, `:61:`, and `:86:` ensures that account information and currency context are preserved for subsequent transactions.
- **Weaknesses:** It is a "practical" parser rather than a full SWIFT-compliant one. It lacks support for multi-line `:86:` tags (only reads the first line) and does not handle complex structured data within the narration.

## 2. Mapping of MT940 Tags
The mapping strategy is sound for Phase 3:
- `:61: Entry Date` & `Value Date` -> `transaction_date` & `value_date`.
- `:61: Amount` -> `amount` (correctly handling comma to dot conversion).
- `:61: Transaction Type` -> `payment_rail` (via a lookup table in the normalizer).
- `:61: Customer Reference` -> `transaction_reference`.
- `:86: Narration` -> `narration`.

## 3. Canonical Model Compatibility
The MT940 data is successfully pivoted into the `CanonicalTransaction` model.
- **Fields matched:** `record_id`, `transaction_reference`, `amount`, `currency`, `direction`, `value_date`.
- **Placeholder usage:** `counterparty_account` is defaulted to `UNKNOWN` as MT940 statement lines often lack this info in a structured way. `status` is defaulted to `SUCCESS`.

## 4. Reconciliation Accuracy
Based on `test_mt940_parser.py`, the engine correctly pairs internal records with MT940 statement lines using exact matching. The logic to use `bank_reference` if `customer_reference` is `NONREF` or empty improves match rates for bank-initiated transactions.

## 5. Potential Edge Cases
- **Multi-line Narration:** SWIFT allows `:86:` to span multiple lines. The current parser only reads the line starting with `:86:`.
- **Currency Context:** The parser relies on `:60F:` or `:62F:` to set the currency. If a statement file contains multiple accounts with different currencies, the state management must be robust.
- **Structured Narration:** Many banks use structured codes in `:86:` (e.g., `/REMT/INV123`). The current parser treats the whole line as a string.

## 6. Test Coverage Quality
- **Current Coverage:** Good. Tests verify amount conversion, direction mapping, and end-to-end reconciliation with internal ledgers.
- **Missing Tests:** 
    - Empty or malformed files.
    - Files with only headers/footers and no transactions.
    - Files with multiple statement blocks.

## 7. Missing SWIFT Features
- **Structured Data Parsing:** Handling `/` delimited fields in `:86:`.
- **Character Set Support:** SWIFT uses a specific character set (X-Character set); the parser assumes UTF-8.
- **Field 61 Detail:** Sub-fields of `:61:` (like `Identification Code`) are largely ignored except for basic rail mapping.

## 8. Risks before Production Use
- **Robustness:** The regex for `:61:` is strict. Variations in bank implementations (which are common in MT940) might cause `MT940ParserError`.
- **Reference Logic:** Relying solely on the `:61:` reference fields might fail if the actual match key is buried in the middle of a structured `:86:` block.
- **Large Files:** `read_text().splitlines()` loads the entire file into memory, which might be an issue for very large monthly statements.
