# ADR 005: Reporting Format Selection

## Status
Accepted

## Context
The engine needs to provide output for both automated systems and human reviewers.

## Decision
- **JSON:** For the summary report (machine-readable).
- **CSV:** For matched/exception lists (easy to open in Excel).
- **Audit Log:** Chronological CSV for compliance.

## Consequences
- **Pros:** Highly portable and lightweight.
- **Cons:** Lacks the formatting and multi-tab capabilities of native Excel files (planned for Phase 5).
