from pathlib import Path


PROJECT_ROOT = Path.cwd()
DEFAULT_GENERATED_DIR = Path("data/generated")
DEFAULT_OUTPUT_DIR = Path("data/output")
DEFAULT_INTERNAL_FILE = DEFAULT_GENERATED_DIR / "internal_ledger.csv"
DEFAULT_EXTERNAL_FILE = DEFAULT_GENERATED_DIR / "bank_settlement.csv"
