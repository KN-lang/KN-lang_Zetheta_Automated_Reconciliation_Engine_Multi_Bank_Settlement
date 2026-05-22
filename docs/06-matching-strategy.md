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

## Phase 2: Enhanced Matching (Planned)

### Fuzzy Reference Matching
Using `rapidfuzz` to handle minor typos in references (e.g., `REF123` vs `REF-123`).

### Amount Tolerance
Configurable thresholds (e.g., match if difference is < $0.05) to account for minor rounding or bank fees.

### Date Windowing
Allowing matches within a +/- 1-3 day window to account for settlement delays.

### Many-to-One / Many-to-Many
Future support for aggregating multiple internal transactions against a single bank bulk settlement.
