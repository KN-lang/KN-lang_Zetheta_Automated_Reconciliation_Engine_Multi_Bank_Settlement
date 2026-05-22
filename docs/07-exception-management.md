# Exception Management

Exceptions are the "breaks" in the reconciliation process. Effective management is critical for operational efficiency.

## Classification Rules (Phase 1)
The engine automatically labels every unmatched record:

1. **Unmatched (Generic):** No record with the same reference was found in the opposing source.
2. **Duplicate Reference:** Multiple records exist with the same reference, creating ambiguity that prevents a safe 1:1 match.
3. **Partial Match (Planned):** Reference found, but other attributes (Amount/Date) differ.

## Exception Workflow
1. **Detection:** Matching engine identifies record as "orphan".
2. **Classification:** `ExceptionClassifier` assigns a reason code.
3. **Reporting:** Record is written to `exceptions.csv` with the `exception_type` field.
4. **Audit:** The audit log records that these records failed to pair.

## Metrics
- **Match Rate:** Percentage of records successfully paired. (Current: **92%**)
- **Exception Count:** Total number of unmatched items. (Current: **16**)
- **Aging (Planned):** Tracking how long an exception remains unresolved across daily runs.
