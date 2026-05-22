# Technology Evaluation

## Core Stack
- **Language:** Python 3.11+
    - *Rationale:* Rich ecosystem for data processing, easy integration with financial formats, and high developer productivity.
- **Data Processing:** Pandas
    - *Rationale:* Industry-standard for tabular data manipulation, providing high performance for Phase 1 CSV processing.
- **Data Validation:** Pydantic
    - *Rationale:* Ensures type safety and strict schema enforcement for the Canonical Data Model.
- **CLI Framework:** Typer
    - *Rationale:* Rapid development of a professional, self-documenting command-line interface.

## Parser Evaluation
- **CSV (Implemented):** Native Python `csv` module and Pandas. Efficient for initial flat-file ingestion.
- **MT940 (Planned):** Evaluating `mt940` or custom regex-based parsers for SWIFT messages.
- **CAMT.053 (Planned):** Evaluating `lxml` for high-performance XML parsing of ISO 20022 statements.

## Matching Engine logic
- **Exact Match (Implemented):** Set-based intersection on (Reference, Amount, Currency, Direction, Date).
- **Fuzzy Match (Planned):** `rapidfuzz` for Levenshtein distance on references and narration.

## Storage & Reporting
- **File-Based (Current):** CSV/JSON for portability and ease of verification in the initial phase.
- **Excel (Planned):** `openpyxl` for generating formatted business reports.

## Evaluation Summary
The selected stack balances performance with flexibility, allowing the engine to scale from simple CSV reconciliation to complex multi-format ingestion while maintaining a strict canonical model for internal processing.
