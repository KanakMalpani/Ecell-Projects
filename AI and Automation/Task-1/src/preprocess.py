"""
Stage 1: load 10-K filings, clean text, extract sections, derive risk labels.

The raw Hugging Face dataset has NO risk labels, so this module:
  1. Downloads filing text from Hugging Face
  2. Cleans messy HTML / boilerplate
  3. Extracts four key sections (Risk Factors, Business, MD&A, Financials)
  4. Scores each filing's Risk Factors section with keyword matching
  5. Splits filings into low / medium / high risk groups

Output: a pandas DataFrame ready for feature engineering in features.py.
"""

from __future__ import annotations

import pandas as pd
from huggingface_hub import hf_hub_download

from .text_preprocessor import get_preprocessor
from .utils import (
    DATASET_NAME,
    DATASET_SPLIT,
    DATASET_SPLIT_FILE,
    DEFAULT_MAX_SAMPLES,
    SECTION_COLUMNS,
    setup_logging,
)

logger = setup_logging(__name__)

# ---------------------------------------------------------------------------
# Keyword lists used to score how risky a filing's Risk Factors section is.
# High-risk words are weighted 3× because they signal serious danger.
# ---------------------------------------------------------------------------
HIGH_RISK_TERMS = (
    "bankruptcy",
    "litigation",
    "default",
    "impairment",
    "covenant",
    "going concern",
    "material weakness",
    "restatement",
    "fraud",
    "delist",
    "substantial doubt",
    "liquidity crisis",
    "indebtedness",
    "adverse effect",
)

MEDIUM_RISK_TERMS = (
    "uncertain",
    "volatile",
    "competition",
    "regulatory",
    "cybersecurity",
    "fluctuation",
    "may not",
    "could adversely",
    "economic downturn",
    "supply chain",
)

# NLTK preprocessor — tokenization, stop-word removal, lemmatization
_preprocessor = get_preprocessor()


def clean_text(text: str) -> str:
    """
    Normalise raw filing text so the model sees clean, consistent input.

    Uses the NLTK TextPreprocessor instead of hardcoded word filters:
      1. Strip HTML tags, entities, and SEC boilerplate (regex)
      2. Tokenize with NLTK word_tokenize
      3. Remove English stop words from NLTK corpus
      4. Lemmatize tokens with WordNet
      5. Rejoin into a single cleaned string
    """
    return _preprocessor.preprocess(text)


def extract_sections(row: dict) -> dict[str, str]:
    """
    Pull the four 10-K sections from one raw dataset record.

    Each section is cleaned independently so we can use them separately
    later (e.g. for custom word-count features).
    """
    sections: dict[str, str] = {}
    for key, column in SECTION_COLUMNS.items():
        raw = row.get(column) or ""
        sections[key] = clean_text(str(raw))
    return sections


def build_document_text(sections: dict[str, str]) -> str:
    """
    Join all four sections into one long string — the model reads this.

    Risk Factors comes first because it carries the strongest risk signal.
    """
    ordered = ("risk_factors", "business", "mda", "financial_statements")
    parts = [sections[name] for name in ordered if sections.get(name)]
    return " ".join(parts).strip()


def compute_risk_score(risk_text: str) -> float:
    """
    Score how risky a filing's Risk Factors section sounds.

    Formula:
      score = (high_hits × 3 + medium_hits × 1) / word_count × 1000

    Multiplying by 1000 just makes the numbers easier to work with.
    A filing mentioning "bankruptcy" and "litigation" scores much higher
    than one that only says "competition" and "uncertain".
    """
    if not risk_text:
        return 0.0

    text = risk_text.lower()
    words = max(len(text.split()), 1)  # avoid division by zero
    high_hits = sum(3.0 for term in HIGH_RISK_TERMS if term in text)
    medium_hits = sum(1.0 for term in MEDIUM_RISK_TERMS if term in text)
    density = (high_hits + medium_hits) / words
    return float(density * 1000.0)


def assign_risk_labels(scores: list[float]) -> list[str]:
    """
    Convert numeric risk scores into low / medium / high labels.

    Uses pd.qcut to split filings into three EQUAL-SIZED groups by rank:
      - bottom third  → "low"
      - middle third  → "medium"
      - top third     → "high"

    If qcut fails (e.g. too few unique scores), falls back to a simple
    median split: above median = high, below = low.
    """
    if not scores:
        return []

    series = pd.Series(scores, dtype=float)
    ranked = series.rank(method="first")
    try:
        buckets = pd.qcut(ranked, 3, labels=["low", "medium", "high"])
        return buckets.astype(str).tolist()
    except ValueError:
        median = float(series.median())
        return ["high" if score >= median else "low" for score in series]


def load_raw_records(max_samples: int = DEFAULT_MAX_SAMPLES) -> list[dict]:
    """
    Download the SEC filings parquet file from Hugging Face and load it.

    Returns a list of dicts — one dict per company filing.
    """
    logger.info(
        "Loading dataset %s split=%s (max_samples=%s)",
        DATASET_NAME,
        DATASET_SPLIT,
        max_samples,
    )
    parquet_path = hf_hub_download(
        DATASET_NAME,
        DATASET_SPLIT_FILE,
        repo_type="dataset",
    )
    frame = pd.read_parquet(parquet_path)
    records = frame.head(max_samples).to_dict(orient="records")
    logger.info("Loaded %s records from %s", len(records), parquet_path)
    return records


def preprocess_records(max_samples: int = DEFAULT_MAX_SAMPLES) -> pd.DataFrame:
    """
    Full preprocessing pipeline: load → clean → score → label.

    Returns a DataFrame with one row per usable filing, including:
      - company_name, filing_date
      - text (combined sections)
      - risk_score (numeric)
      - risk_label (low / medium / high)
      - individual section texts (for custom features later)
    """
    rows: list[dict] = []
    risk_scores: list[float] = []

    for record in load_raw_records(max_samples=max_samples):
        sections = extract_sections(record)
        document_text = build_document_text(sections)

        # Skip filings that are too short to be useful after cleaning
        if len(document_text.split()) < 30:
            continue

        # Risk keyword scoring uses markup-stripped text (keeps phrases like "going concern")
        raw_risk = str(record.get("Risk Factors") or "")
        risk_score = compute_risk_score(_preprocessor.strip_markup(raw_risk))
        risk_scores.append(risk_score)
        rows.append(
            {
                "company_name": record.get("company_name", ""),
                "filing_date": str(record.get("filing_date", "")),
                "text": document_text,
                "risk_score": risk_score,
                "section_risk_factors": sections.get("risk_factors", ""),
                "section_business": sections.get("business", ""),
                "section_mda": sections.get("mda", ""),
                "section_financials": sections.get("financial_statements", ""),
            }
        )

    if not rows:
        raise ValueError("No usable records after preprocessing.")

    # Assign labels AFTER collecting all scores so qcut can rank them fairly
    labels = assign_risk_labels(risk_scores)
    frame = pd.DataFrame(rows)
    frame["risk_label"] = labels
    logger.info("Prepared %s records with label distribution:\n%s", len(frame), frame["risk_label"].value_counts())
    return frame


def save_processed(frame: pd.DataFrame, path) -> None:
    """Save the processed DataFrame to a CSV file for inspection / reuse."""
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    logger.info("Saved processed data to %s", path)
