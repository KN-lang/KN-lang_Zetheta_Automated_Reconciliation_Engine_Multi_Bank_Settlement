# Development Plan

## Phase 1: CSV Reconciliation

- Generate simulated internal ledger and bank settlement CSV files.
- Parse and validate required CSV columns.
- Normalize both source formats into the canonical transaction schema.
- Apply exact matching on transaction reference, amount, currency, direction, and same-day value date.
- Classify first-pass exceptions with deterministic rules.
- Write matched records, exceptions, summary, and audit log outputs.

## Phase 2: Fuzzy Matching

- Status: Implemented.
- Added configurable amount tolerances.
- Added date tolerance windows.
- Added fuzzy reference, narration, and counterparty matching with `rapidfuzz`.
- Added weighted confidence scoring and review queue generation.
- Added Excel workbook output with Summary, Matched, Exceptions, Review Queue, and Audit Log sheets.

## Phase 3: MT940 Parser

- Parse MT940 statements into intermediate records.
- Normalize statement lines into canonical transactions.
- Add parser-specific tests with realistic statement samples.

## Phase 4: CAMT.053 Parser

- Parse ISO 20022 CAMT.053 XML files with namespace-aware XML handling.
- Normalize entries and transaction details into canonical transactions.
- Validate parser behavior against sample bank files.

## Phase 5: Reports and Dashboard

- Enhance Excel report formatting and analyst workflow support.
- Add richer audit output.
- Consider a lightweight dashboard for reconciliation operations.

## Phase 6: Performance Benchmarking

- Benchmark large CSV loads and matching operations.
- Profile memory usage.
- Add capacity planning guidance for settlement volumes.
