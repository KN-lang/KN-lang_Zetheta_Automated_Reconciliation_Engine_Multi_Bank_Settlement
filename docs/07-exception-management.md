# Exception Management

Exceptions are the "breaks" in the reconciliation process. Effective management is critical for operational efficiency.

## Classification Rules
The engine automatically labels records that are not auto-matched or placed in the review queue:

1. **Missing Internal / Missing External:** No record with the same reference was found in the opposing source.
2. **Duplicate Reference:** Multiple records exist with the same reference, creating ambiguity that prevents a safe 1:1 match.
3. **Attribute Mismatch:** Reference found, but amount, date, currency, or direction differs.
4. **Review Required:** In fuzzy mode, medium-confidence candidate pairs are written to `review_queue.csv` rather than treated as final exceptions.

## Exception Workflow
1. **Detection:** Matching engine identifies record as "orphan".
2. **Classification:** `ExceptionClassifier` assigns a reason code.
3. **Review Queue:** If fuzzy matching is enabled and the confidence score falls between review thresholds, the pair is written to `review_queue.csv`.
4. **Reporting:** Remaining exceptions are written to `exceptions.csv` with the `exception_category` field.
5. **Audit:** The audit log records matching, review queue, and exception classification stages.

## Metrics
- **Match Rate:** Percentage of records successfully auto-matched.
- **Review Rate:** Percentage of records routed to analyst review.
- **Exception Count:** Total number of unmatched or duplicate exception rows.
- **Aging (Planned):** Tracking how long an exception remains unresolved across daily runs.
