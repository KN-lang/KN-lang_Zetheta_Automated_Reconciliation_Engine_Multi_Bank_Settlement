# Scalability and Performance

## Current Performance (Phase 1)
- **Volume:** 200 records (100 internal / 100 external).
- **Processing Time:** < 1 second.
- **Method:** In-memory Pandas processing.

## Scalability Strategy

### 1. Memory Efficiency
- For volumes up to 1 million records, Pandas in-memory processing is sufficient on standard hardware (16GB RAM).
- Use of categorical dtypes for Currency and Direction to reduce memory footprint.

### 2. Matching Optimization
- Current exact matching uses Hash Sets/Dictionaries, which is **O(n)** complexity.
- Fuzzy matching (Planned) will introduce **O(n log n)** or **O(n^2)** complexity; optimization using blocking or indexing on the first character of references will be explored.

### 3. Parallel Processing
- The normalization step is "Embarrassingly Parallel". We can use Python's `multiprocessing` to normalize large files across multiple CPU cores before matching.

### 4. Database Integration (Future)
- For extreme volumes or long-term storage, the engine can be extended to use an SQL backend (PostgreSQL) for persistence and query-based matching.
