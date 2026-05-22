# Canonical Data Model

To support multi-bank ingestion (CSV, MT940, CAMT.053), the engine uses a unified internal representation.

## CanonicalTransaction (Pydantic Model)

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | `str` | Unique identifier generated during normalization. |
| `amount` | `Decimal` | Transaction amount (precision: 2 decimals). |
| `currency` | `str` | ISO 4217 currency code (e.g., USD, EUR). |
| `reference` | `str` | Transaction reference or UETR. |
| `date` | `date` | Value date of the transaction. |
| `direction` | `Enum` | `CREDIT` (Inflow) or `DEBIT` (Outflow). |
| `metadata` | `dict` | Source-specific fields (e.g., bank account number). |

## Design Rationale
- **Decimals for Currency:** Avoids floating-point errors common in financial calculations.
- **Strict Typing:** Pydantic ensures that a "date" is a valid date before it reaches the matching engine.
- **Source Agnostic:** Whether the data comes from a legacy CSV or a modern XML CAMT.053, it must conform to this model.

## Normalization Examples

### Internal CSV -> Canonical
- `TXN_ID` -> `transaction_id`
- `Amount` -> `amount`
- `Ref` -> `reference`

### MT940 -> Canonical (Planned)
- Tag `:61:` (Statement Line) -> `amount`, `date`, `direction`.
- Tag `:86:` (Information to Account Owner) -> `reference`.
