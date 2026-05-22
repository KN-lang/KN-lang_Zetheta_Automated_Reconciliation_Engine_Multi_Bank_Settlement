# Capacity Planning

## Hardware Estimates

| Volume (Txns/Day) | RAM | CPU | Storage |
|-------------------|-----|-----|---------|
| 10,000 | 4 GB | 1 Core | 100 MB |
| 100,000 | 8 GB | 2 Cores | 1 GB |
| 1,000,000 | 32 GB | 8 Cores | 10 GB |

## Data Retention
- **Audit Logs:** Should be retained for 7 years per financial regulations.
- **Input Files:** Archived in compressed format (zip/gzip) after successful reconciliation.

## Scaling Limits
- **Vertical Scaling:** Increase RAM to handle larger Pandas DataFrames.
- **Horizontal Scaling:** Partition data by "Bank Account" or "Entity" and run multiple reconciliation instances in parallel.
