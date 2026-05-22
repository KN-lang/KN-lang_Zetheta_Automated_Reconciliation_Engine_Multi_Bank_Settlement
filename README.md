# Automated Reconciliation Engine

Python foundation for a multi-bank settlement reconciliation engine. Phase 1 implements an end-to-end CSV pipeline: sample data generation, parsing, normalization, exact matching, exception classification, and report output.

## Architecture

- `parsers`: CSV loading and required-column validation.
- `normalisation`: source-specific mappings into the canonical transaction schema.
- `matching`: exact one-to-one matching.
- `exceptions`: deterministic rule-based exception classification.
- `reports`: CSV and JSON output writers plus audit logging.
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
- `data/output/summary.json`
- `data/output/audit_log.csv`

`summary.json` includes record counts, matched count, exception count, match rate, exception breakdown, and generation timestamp.

## Current Limitations

- Matching is exact only.
- Duplicate references are excluded from exact matching and classified as exceptions.
- Amount matching uses two-decimal `Decimal` values, but no tolerance rules yet.
- MT940 and CAMT.053 parsers are planned but not implemented in Phase 1.
- Reports are CSV/JSON only; Excel and dashboards are later phases.

## Next Milestones

1. Add fuzzy reference matching and configurable tolerances.
2. Implement MT940 parsing.
3. Implement CAMT.053 XML parsing.
4. Add Excel reports and operational dashboards.
5. Benchmark performance on larger transaction volumes.
