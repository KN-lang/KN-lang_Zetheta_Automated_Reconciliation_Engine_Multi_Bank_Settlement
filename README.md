# Automated Reconciliation Engine

Automated Reconciliation Engine for multi-bank settlement systems. The project ingests internal ledger CSV files and external bank settlement data from CSV, simulated MT940, and simulated CAMT.053 XML, normalizes them into a canonical transaction schema, applies exact and fuzzy/tolerance matching, classifies exceptions, and writes analyst-ready reports.

This is an assignment-grade fintech/data-engineering implementation. It is modular and testable, but it does not claim full production banking-format certification.
## Business Context

Financial institutions maintain an internal ledger of transactions while receiving settlement statements from banks and payment networks.

Differences can occur due to timing delays, duplicate entries, missing records, amount mismatches, settlement failures, or formatting inconsistencies.

The purpose of this engine is to automatically compare internal and external transaction records, identify matches, classify discrepancies, and generate actionable reconciliation reports for analysts and operations teams.

Internal Ledger CSV
        │
        ▼
   Normalization
        │
        ▼
 Matching Engine
 (Exact + Fuzzy)
        │
 ┌──────┴──────┐
 ▼             ▼
Matched     Exceptions
 ▼             ▼
Reports   Review Queue

## Features

| Area | Status |
|---|---|
| Internal ledger CSV ingestion | Implemented |
| Bank settlement CSV ingestion | Implemented |
| MT940 statement ingestion | Implemented for simulated/common `:61:` and `:86:` lines |
| CAMT.053 XML ingestion | Implemented for simulated/common `<Ntry>` records |
| Canonical transaction model | Implemented |
| Exact matching | Implemented |
| Fuzzy/tolerance matching | Implemented with `rapidfuzz` |
| Confidence scoring | Implemented |
| Review queue | Implemented |
| Exception classification | Implemented |
| CSV/JSON reports | Implemented |
| Excel workbook report | Implemented |
| Benchmark command | Implemented |
| Test suite | 22 tests passing |

## Supported Formats

| Format | Input | CLI value | Notes |
|---|---|---|---|
| Internal ledger | CSV | internal input | Required for all reconciliations |
| Bank settlement | CSV | `csv` | Primary Phase 1 format |
| SWIFT MT940 | `.mt940` text | `mt940` | Practical parser, not full SWIFT compliance |
| ISO 20022 CAMT.053 | XML | `camt053` | Namespace-tolerant practical parser |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If your shell only exposes `python3`, use `.venv/bin/python` after creating the virtual environment.

## Generate Sample Data

```bash
python -m recon_engine generate-sample-data --include-mt940 --include-camt053
```

Outputs:

- `data/generated/internal_ledger.csv`
- `data/generated/bank_settlement.csv`
- `data/generated/bank_statement.mt940`
- `data/generated/bank_statement_camt053.xml`

## Reconcile CSV

```bash
python -m recon_engine reconcile \
  --internal data/generated/internal_ledger.csv \
  --external data/generated/bank_settlement.csv \
  --external-format csv \
  --output data/output \
  --enable-fuzzy
```

## Reconcile MT940

```bash
python -m recon_engine reconcile \
  --internal data/generated/internal_ledger.csv \
  --external data/generated/bank_statement.mt940 \
  --external-format mt940 \
  --output data/output \
  --enable-fuzzy
```

## Reconcile CAMT.053

```bash
python -m recon_engine reconcile \
  --internal data/generated/internal_ledger.csv \
  --external data/generated/bank_statement_camt053.xml \
  --external-format camt053 \
  --output data/output \
  --enable-fuzzy
```

## Benchmark

```bash
python -m recon_engine benchmark --records 1000
```

Outputs:

- `reports/benchmark_results.md`
- `data/output/benchmark_summary.json`

## Report Outputs

Each reconciliation run writes:

- `data/output/matched.csv`
- `data/output/exceptions.csv`
- `data/output/review_queue.csv`
- `data/output/summary.json`
- `data/output/audit_log.csv`
- `data/output/reconciliation_report.xlsx`

Sample summary fields:

```json
{
  "matched_count": 94,
  "exact_match_count": 91,
  "fuzzy_match_count": 1,
  "tolerance_match_count": 2,
  "review_required_count": 2,
  "match_rate_percent": 94.0,
  "external_format": "csv"
}
```

## Architecture

- `src/recon_engine/parsers`: CSV, MT940, and CAMT.053 parsers.
- `src/recon_engine/normalisation`: source-specific mapping into the canonical schema.
- `src/recon_engine/matching`: exact and fuzzy/tolerance matching.
- `src/recon_engine/exceptions`: deterministic exception classification.
- `src/recon_engine/reports`: CSV, JSON, Excel, summary, and audit outputs.
- `src/recon_engine/simulation`: synthetic data generation.
- `src/recon_engine/benchmark.py`: laptop-scale benchmark runner.

## Documentation Index

See [docs/README.md](docs/README.md) for the full documentation map, including scenario analysis, technology evaluation, design docs, matching strategy, exception management, ingestion notes, scalability, capacity planning, FMEA, and architecture review.

## Tests

```bash
pytest
```

Current suite: 22 tests covering normalization, exact matching, fuzzy scoring, tolerance behavior, review queue, Excel report creation, MT940 parsing, CAMT.053 parsing, and exception handling.

## Limitations

- MT940 and CAMT.053 parsers are practical assignment parsers, not full standard-compliance engines.
- Fuzzy thresholds are configurable but not calibrated against production bank data.
- Matching is one-to-one; many-to-one settlement aggregation is future work.
- Dashboard, streaming ingestion, auth, persistence, and production deployment are out of scope.
