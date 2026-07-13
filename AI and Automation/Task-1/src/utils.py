"""
Shared configuration, paths, and logging helpers.

WHAT THIS FILE DOES
-------------------
Centralizes every cross-cutting constant and utility used by the pipeline:
folder paths, Hugging Face dataset identifiers, 10-K section column names,
risk label ordering, random seed, and logging setup.

WHY IT EXISTS
-------------
Without a single source of truth, dataset names and paths get copy-pasted
across modules — a common source of bugs (wrong column name, inconsistent
random seed breaking reproducibility). One file to import from everywhere.

HOW IT FITS IN THE PIPELINE
---------------------------
  Imported by virtually every src/ module and run_pipeline.py.
  Does NOT contain ML logic — pure configuration and helpers.

Consumers:
  preprocess.py  → DATASET_NAME, SECTION_COLUMNS, DEFAULT_MAX_SAMPLES
  features.py    → MODELS_DIR
  train.py       → MODELS_DIR, RISK_LABELS, RANDOM_STATE
  evaluate.py    → MODELS_DIR, REPORTS_DIR, RANDOM_STATE, save_json
  run_pipeline.py → DATA_DIR, REPORTS_DIR, ensure_dirs, setup_logging

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Reproducibility: RANDOM_STATE=42 fixes train/test split across runs.
  2. Path abstraction: PROJECT_ROOT derived from __file__ — works regardless
     of where you invoke python from.
  3. Hugging Face dataset: winterForestStump/10-K_sec_filings, parquet shard.
  4. SECTION_COLUMNS: maps logical keys to exact HF column names (MD&A has
     unicode apostrophe in column name).
  5. RISK_LABELS tuple order: defines consistent label→integer encoding.
  6. ensure_dirs(): idempotent directory creation before pipeline writes.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Project folder paths (relative to Task-1 root)
#
# PROJECT_ROOT is computed from this file's location (src/utils.py → parent.parent)
# so imports work whether you run from Task-1/ or elsewhere.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"       # processed_filings.csv
MODELS_DIR = PROJECT_ROOT / "models"   # .joblib model + vectorizer artifacts
REPORTS_DIR = PROJECT_ROOT / "reports" # evaluation JSON, CSV, confusion PNGs

# ---------------------------------------------------------------------------
# Hugging Face dataset configuration
#
# Dataset: SEC 10-K filings with pre-extracted sections as parquet columns.
# Split "026" refers to a specific shard file in the dataset repository.
# ---------------------------------------------------------------------------
DATASET_NAME = "winterForestStump/10-K_sec_filings"
DATASET_SPLIT = "026"
DATASET_SPLIT_FILE = "data/026-00000-of-00001-617edf0addd6f69e.parquet"

# ---------------------------------------------------------------------------
# 10-K section column mapping
#
# Keys are internal names used throughout the pipeline; values are exact
# column headers in the Hugging Face parquet file.
# MDA_COLUMN uses Unicode right single quotation mark (U+2019) in "Management's".
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Classification constants
# ---------------------------------------------------------------------------
RISK_LABELS = ("low", "medium", "high")  # canonical label order for encoding

DEFAULT_MAX_SAMPLES = 800  # filings to load unless --max-samples overrides

RANDOM_STATE = 42  # fixes sklearn train_test_split for reproducible experiments


# ---------------------------------------------------------------------------
# Logging setup — consistent timestamped console output across all modules
# ---------------------------------------------------------------------------
def setup_logging(name: str = "10k_pipeline") -> logging.Logger:
    """
    Create a logger that prints timestamped INFO messages to stderr.

    Idempotent: if handlers already exist on this named logger, returns it
    without adding duplicates (important when modules import each other).

    Args:
        name: Logger name — typically __name__ of calling module.

    Returns:
        Configured logging.Logger instance.

    Example output:
        2026-06-15 10:00:00 | INFO | Loaded 800 records from ...
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger


# ---------------------------------------------------------------------------
# Filesystem helpers
# ---------------------------------------------------------------------------
def ensure_dirs() -> None:
    """
    Create data/, models/, and reports/ directories if they do not exist.

    Called at pipeline start by run_pipeline.py before any writes.
    parents=True handles nested path creation; exist_ok=True is idempotent.
    """
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: dict) -> None:
    """
    Write a Python dictionary to a JSON file with pretty indentation.

    Used by evaluate.py for evaluation_report.json persistence.

    Args:
        path: Target file path (parent dirs created if needed).
        payload: Serializable dict (metrics, confusion matrices, etc.).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
