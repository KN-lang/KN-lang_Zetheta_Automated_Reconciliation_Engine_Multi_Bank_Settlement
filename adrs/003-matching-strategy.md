# ADR 003: Matching Strategy

## Status
Accepted

## Context
Initial requirements demand high precision for settlement reconciliation.

## Decision
Phase 1 will implement **Exact Matching** only. A match requires identical Reference, Amount, Currency, Direction, and Date.

## Consequences
- **Pros:** Zero false positives.
- **Cons:** High volume of exceptions due to minor typos or formatting differences, which will be addressed in Phase 2 (Fuzzy Matching).
