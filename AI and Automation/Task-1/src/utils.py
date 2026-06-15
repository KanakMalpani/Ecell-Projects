"""
Shared configuration, paths, and logging helpers.

Every other module imports from here so folder locations and dataset
settings live in ONE place instead of being copy-pasted everywhere.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Folder paths (relative to the Task-1 project root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # .../Task-1/
DATA_DIR = PROJECT_ROOT / "data"       # processed CSV files
MODELS_DIR = PROJECT_ROOT / "models"   # saved .joblib model files
REPORTS_DIR = PROJECT_ROOT / "reports" # metrics, confusion matrices

# ---------------------------------------------------------------------------
# Hugging Face dataset settings
# ---------------------------------------------------------------------------
DATASET_NAME = "winterForestStump/10-K_sec_filings"
DATASET_SPLIT = "026"
# Exact parquet file inside the dataset repo on Hugging Face Hub
DATASET_SPLIT_FILE = "data/026-00000-of-00001-617edf0addd6f69e.parquet"

# Column names in the raw dataset for each 10-K section we care about
MDA_COLUMN = (
    "Management\u2019s Discussion and Analysis of Financial Condition and Results"
    " of Operations"
)
FINANCIALS_COLUMN = "Financial Statements and Supplementary Data"

SECTION_COLUMNS = {
    "business": "Business",
    "risk_factors": "Risk Factors",
    "mda": MDA_COLUMN,
    "financial_statements": FINANCIALS_COLUMN,
}

# The three risk classes our model predicts
RISK_LABELS = ("low", "medium", "high")

# How many filings to download by default (use --max-samples to override)
DEFAULT_MAX_SAMPLES = 800

# Fixed random seed so train/test splits are reproducible across runs
RANDOM_STATE = 42


def setup_logging(name: str = "10k_pipeline") -> logging.Logger:
    """
    Create a logger that prints timestamped INFO messages to the terminal.

    Example output:
        2026-06-15 10:00:00 | INFO | Loaded 800 records from ...
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured — don't add duplicate handlers

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger


def ensure_dirs() -> None:
    """Create data/, models/, and reports/ folders if they don't exist yet."""
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: dict) -> None:
    """Write a Python dictionary to a JSON file (used for evaluation reports)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
