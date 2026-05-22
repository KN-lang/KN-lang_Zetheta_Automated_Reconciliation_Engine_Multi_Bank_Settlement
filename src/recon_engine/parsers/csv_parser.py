from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import pandas as pd

logger = logging.getLogger(__name__)


class CSVParserError(ValueError):
    """Raised when a CSV cannot be loaded or validated."""


def read_csv(path: str | Path, required_columns: Iterable[str]) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise CSVParserError(f"CSV file not found: {csv_path}")

    try:
        frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
    except Exception as exc:  # pandas raises several parser-specific exceptions
        raise CSVParserError(f"Failed to read CSV {csv_path}: {exc}") from exc

    missing = sorted(set(required_columns) - set(frame.columns))
    if missing:
        raise CSVParserError(f"CSV {csv_path} is missing required columns: {missing}")

    logger.info("Loaded CSV %s with %s records", csv_path, len(frame))
    return frame
