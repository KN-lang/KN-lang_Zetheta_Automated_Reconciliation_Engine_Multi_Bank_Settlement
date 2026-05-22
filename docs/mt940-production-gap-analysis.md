# MT940 Production Gap Analysis

## Overview
Phase 3 has successfully integrated MT940 parsing into the reconciliation pipeline. However, several "Real World" gaps exist that must be addressed before the engine can be deployed for production multi-bank reconciliation.

## Strengths
- **Decoupled Architecture:** The matching engine remains format-agnostic.
- **Accurate Normalization:** Correct handling of financial precision (Decimal) and MT940 date formats.
- **Auditability:** MT940 source lines are hashed and linked to canonical records.

## Weaknesses & Gaps
1. **Limited Tag Support:** Only supports a subset of SWIFT tags. Missing support for `:62M:`, `:64:`, etc., which are used for balance verification.
2. **Narration Truncation:** Fails to capture multi-line `:86:` tags, leading to lost data that might be needed for fuzzy matching.
3. **Reference Variability:** Different banks populate `:61:` references differently. Some put the UTR in `:86:`, which is not yet parsed for references.
4. **Error Handling:** Current error messages are helpful but the parser is "brittle" to small formatting deviations.

## Recommendations
- **Switch to Library:** For production, consider using a robust library like `mt940` (python-mt940) instead of custom regex to handle the vast complexity of SWIFT message variations.
- **Enhanced Reference Extraction:** Implement "Reference Hunting" in narration strings to extract UETRs/UTRs when the standard reference fields are empty.
- **Balance Validation:** Implement a check where `Opening Balance + Sum(Transactions) == Closing Balance` to ensure no records were missed during parsing.

## Production Roadmap
- [ ] **Sprint 1:** Implement multi-line tag support and balance validation logic.
- [ ] **Sprint 2:** Add "Reference Hunting" regex for narration fields.
- [ ] **Sprint 3:** Stress test with 100MB+ statement files and profile memory usage.
- [ ] **Sprint 4:** Pilot with a single bank's actual production MT940 export (masked data).
- [ ] **Sprint 5:** Implement support for structured `:86:` fields (e.g., SWIFT/SEPA specific codes).
