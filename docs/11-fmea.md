# Failure Mode and Effects Analysis (FMEA)

| Process Step | Potential Failure Mode | Potential Cause | Impact | Mitigation Strategy |
|--------------|------------------------|-----------------|--------|----------------------|
| Ingestion | Invalid File Format | User uploaded wrong file | Process crash | Strict schema validation with Pydantic; clear error messages. |
| Ingestion | Missing Columns | Source system change | Incomplete matching | Required-column check before normalization. |
| Normalization | Date/Amount Parsing Error | Locale differences (e.g., 1.000,00 vs 1,000.00) | Incorrect values | Configurable locale-aware parsers; fallback to strict ISO formats. |
| Matching | High False Positives | Weak reference logic | Financial inaccuracy | Require multiple points of match (Ref + Amt + Date). |
| Matching | Match Collision | Non-unique references | Incorrect pairings | Detection of duplicate references; move to exceptions for manual review. |
| Reporting | Data Loss | Disk full / Write error | Audit failure | Atomic writes; check disk space before execution. |
| Overall | Performance Bottleneck | Huge file size | Timeout/OOM | Implement chunked processing and memory profiling. |
