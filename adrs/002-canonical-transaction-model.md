# ADR 002: Canonical Transaction Model

## Status
Accepted

## Context
To support multiple bank formats (MT940, CAMT.053, CSV), the matching engine should not depend on source-specific field names.

## Decision
Implement a `CanonicalTransaction` pydantic model that serves as the "Universal Language" within the engine. All input data must be normalized into this model before matching.

## Consequences
- **Pros:** Matching logic remains simple and reusable across different banks.
- **Cons:** Requires a custom normalizer for every new source format added.
