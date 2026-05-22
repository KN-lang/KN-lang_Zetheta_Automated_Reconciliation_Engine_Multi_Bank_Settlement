# Benchmark Results

- Generated at: `2026-05-22T09:11:18.737379+00:00`
- Requested records: `1000`

| Benchmark | Format | Records | Seconds | Records/sec | Matched | Review | Exceptions |
|---|---:|---:|---:|---:|---:|---:|---:|
| sample_generation | csv+mt940+camt053 | 1000 | 0.027 | 37091.13 |  |  |  |
| csv_fuzzy | csv | 2000 | 5.5519 | 360.24 | 994 | 2 | 8 |
| mt940_fuzzy | mt940 | 1037 | 35.6125 | 29.12 | 30 | 4 | 969 |
| camt053_fuzzy | camt053 | 1037 | 34.7146 | 29.87 | 30 | 4 | 969 |

These results are laptop-scale smoke benchmarks, not production capacity claims.