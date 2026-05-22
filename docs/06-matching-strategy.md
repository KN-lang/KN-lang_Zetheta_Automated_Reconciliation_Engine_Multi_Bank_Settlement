# Matching Strategy

## Phase 1: Exact Matching (Implemented)
The current engine employs a "Strict Pair" matching strategy.

### Logic
A match is confirmed if and only if the following fields are identical:
1. **Reference:** Must match exactly (case-sensitive in Phase 1).
2. **Amount:** Must be identical (e.g., 100.00 == 100.00).
3. **Currency:** Must match (e.g., USD == USD).
4. **Direction:** Must align (Internal Credit matches External Credit).
5. **Value Date:** Must be on the same day.

### Uniqueness Constraint
The engine handles 1:1 matching. If multiple records share the same reference but different amounts, the engine only pairs those that align perfectly.

---

## Phase 2: Enhanced Matching (Implemented)

### Fuzzy Reference Matching
The optional fuzzy pass uses `rapidfuzz` after exact matching. It compares:

- transaction reference
- narration
- counterparty account
- amount
- currency
- direction
- value date

The text component is driven primarily by transaction reference, with narration and counterparty account used to improve confidence when references are similar but not identical.

### Amount Tolerance
The CLI supports `--amount-tolerance`, defaulting to `1.00`. Amount comparisons are Decimal-safe and do not rely on float equality.

### Date Windowing
The CLI supports `--date-tolerance-days`, defaulting to `2`. Same-day matches get full date confidence; near dates receive partial confidence.

### Confidence Score
The fuzzy matcher uses a weighted score:

- reference/text similarity: 40%
- amount match or tolerance: 25%
- date proximity: 15%
- direction match: 10%
- currency match: 10%

Decision thresholds:

- `score >= 0.85`: auto-match
- `0.60 <= score < 0.85`: review queue
- `score < 0.60`: unmatched

### Many-to-One / Many-to-Many
Future support for aggregating multiple internal transactions against a single bank bulk settlement.

## Phase 3: MT940 External Records (Implemented)

MT940 statement lines are parsed and normalized into the same canonical schema as CSV bank settlement rows. The matching engine does not need a separate MT940 algorithm; exact and fuzzy matching operate on canonical fields such as transaction reference, amount, currency, direction, value date, narration, and source system.

MT940-specific caveats:

- Counterparty account is set to `UNKNOWN` when the statement line does not provide it.
- Payment rail is inferred from MT940 transaction type where practical, otherwise `UNKNOWN`.
- Reference fallback uses bank reference or generated record id when the customer reference is `NONREF`.

## Phase 4: CAMT.053 External Records (Implemented)

CAMT.053 entries are parsed and normalized into the same canonical schema before matching. The matching engine remains source-agnostic: CSV, MT940, and CAMT.053 all flow through exact matching first, then optional fuzzy/tolerance matching.

CAMT.053-specific caveats:

- Transaction reference prefers `EndToEndId`, then `AcctSvcrRef`, then a generated record id.
- Counterparty account is extracted from related party account fields when available.
- Payment rail is inferred from remittance text when it contains known rails such as UPI, NEFT, RTGS, IMPS, or CARD.
- Parser coverage is practical and namespace-tolerant, not full ISO 20022 certification.
