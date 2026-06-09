"""Shared configuration, paths, and logging helpers."""

from __future__ import annotations

import json
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
REPORTS_DIR = PROJECT_ROOT / "reports"

DATASET_NAME = "winterForestStump/10-K_sec_filings"
DATASET_SPLIT = "026"
DATASET_SPLIT_FILE = "data/026-00000-of-00001-617edf0addd6f69e.parquet"

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

RISK_LABELS = ("low", "medium", "high")
DEFAULT_MAX_SAMPLES = 800
RANDOM_STATE = 42


def setup_logging(name: str = "10k_pipeline") -> logging.Logger:
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


def ensure_dirs() -> None:
    for path in (DATA_DIR, MODELS_DIR, REPORTS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
