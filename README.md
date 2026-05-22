# Automated Reconciliation Engine

Python foundation for a multi-bank settlement reconciliation engine. Phase 2 now implements an end-to-end CSV pipeline with exact matching, fuzzy/tolerance matching, confidence scoring, review queue generation, exception classification, and CSV/JSON/Excel report output.

## Architecture

- `parsers`: CSV loading and required-column validation.
- `normalisation`: source-specific mappings into the canonical transaction schema.
- `matching`: exact one-to-one matching plus optional fuzzy and tolerance-based matching.
- `exceptions`: deterministic rule-based exception classification.
- `reports`: CSV, JSON, Excel, review queue, and audit output writers.
- `simulation`: sample internal ledger and bank settlement data generation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Commands

Generate sample files:

```bash
python -m recon_engine generate-sample-data
```

Run reconciliation:

```bash
python -m recon_engine reconcile \
  --internal data/generated/internal_ledger.csv \
  --external data/generated/bank_settlement.csv \
  --output data/output
```

Run reconciliation with fuzzy and tolerance matching:

```bash
python -m recon_engine reconcile \
  --internal data/generated/internal_ledger.csv \
  --external data/generated/bank_settlement.csv \
  --output data/output \
  --enable-fuzzy \
  --amount-tolerance 1.00 \
  --date-tolerance-days 2 \
  --min-auto-score 0.85 \
  --min-review-score 0.60
```

Console script equivalent:

```bash
recon-engine generate-sample-data
recon-engine reconcile --internal data/generated/internal_ledger.csv --external data/generated/bank_settlement.csv --output data/output
```

Run tests:

```bash
pytest
```

## Outputs

The reconciliation command writes:

- `data/output/matched.csv`
- `data/output/exceptions.csv`
- `data/output/review_queue.csv`
- `data/output/summary.json`
- `data/output/audit_log.csv`
- `data/output/reconciliation_report.xlsx`

`summary.json` includes total records, exact/fuzzy/tolerance match counts, auto-match count, review-required count, unmatched count, match rate, review rate, exception breakdown, and generation timestamp.

## Current Limitations

- Fuzzy/tolerance matching is implemented as a one-to-one second pass after exact matching.
- Duplicate references are excluded from exact matching and classified as exceptions.
- Amount comparison uses `Decimal`; fuzzy confidence scores are threshold-based and should be tuned with production data.
- MT940 and CAMT.053 parsers are planned but not implemented yet.
- Dashboards and streaming ingestion are not implemented.

## Next Milestones

1. Implement MT940 parsing.
2. Implement CAMT.053 XML parsing.
3. Expand Excel reports with analyst-friendly formatting and exception aging.
4. Add operational dashboards.
5. Benchmark performance on larger transaction volumes.
