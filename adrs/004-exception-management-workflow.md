# ADR 004: Exception Management Workflow

## Status
Accepted

## Context
Unmatched records need to be categorized to help operational teams prioritize resolution.

## Decision
Use a deterministic `ExceptionClassifier` that assigns specific types (e.g., `DUPLICATE_REFERENCE`, `UNMATCHED`) to records that fail to pair.

## Consequences
- **Pros:** Faster triaging of breaks.
- **Cons:** Requires maintenance of classification rules as new edge cases are discovered.
