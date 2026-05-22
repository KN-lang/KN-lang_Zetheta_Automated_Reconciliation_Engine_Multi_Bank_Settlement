# Data Flow Design

## Step-by-Step Data Flow

### 1. Source Acquisition
Data is gathered from two sources:
- **Internal Ledger:** The "Golden Source" representing what the company expects.
- **External Settlement:** The bank's record of what actually occurred.

### 2. Ingestion & Validation
- Files are loaded via `CSVParser`.
- Schema validation ensures columns like `amount`, `reference`, and `date` exist.

### 3. Normalization (The Pivot Point)
- `Normalizer` converts diverse source schemas into the `CanonicalTransaction` pydantic model.
- **Fields:** `transaction_id`, `amount`, `currency`, `reference`, `date`, `direction` (CREDIT/DEBIT).

### 4. Matching Process
- **Phase 1 (Current):** 
    1. Records are grouped by `reference`.
    2. Within each reference group, the engine looks for exact matches on (Amount, Currency, Direction, Date).
    3. Successfully paired records are moved to the `Matched` bucket.

### 5. Exception Classification
- Unmatched records are analyzed by the `ExceptionClassifier`.
- **Rules:**
    - `DUPLICATE_REFERENCE`: Multiple records with the same reference that couldn't be uniquely paired.
    - `AMOUNT_MISMATCH`: Reference matches but amount differs (planned for fuzzy).
    - `UNMATCHED`: No corresponding record found.

### 6. Final Persistence
- **matched.csv:** All paired records.
- **exceptions.csv:** Categorized breaks.
- **summary.json:** High-level metrics for dashboard ingestion.
- **audit_log.csv:** Sequence of operations for traceability.
