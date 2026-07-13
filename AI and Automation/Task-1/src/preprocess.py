"""
Stage 1: load 10-K filings, clean text, extract sections, derive risk labels.

WHAT THIS FILE DOES
-------------------
Turns raw Hugging Face SEC filing records into a clean, labeled DataFrame
ready for feature engineering. This is the data foundation of the entire
pipeline.

WHY IT EXISTS
-------------
The Hugging Face dataset (winterForestStump/10-K_sec_filings) provides raw
HTML-heavy text but NO risk labels. We must:
  1. Download and parse filings
  2. Clean noisy markup and boilerplate
  3. Extract semantically distinct 10-K sections
  4. Create proxy labels via keyword scoring (weak supervision)

HOW IT FITS IN THE PIPELINE
---------------------------
  First stage called by run_pipeline.py.
  Output → data/processed_filings.csv + in-memory DataFrame for features.py
  Also imported by api/app.py for clean_text() and build_document_text() at
  inference time.

Pipeline within this module:
  load_raw_records() → extract_sections() → build_document_text()
  → compute_risk_score() → assign_risk_labels() → DataFrame

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Weak supervision: labels derived from keyword rules, not human annotators.
     Honest limitation — model learns our scoring function's biases.
  2. Risk Factors section is the primary signal for BOTH labeling and content.
  3. Keyword weighting: high-risk terms ×3, medium ×1 — reflects severity.
  4. pd.qcut for tercile labels: forces balanced classes (equal counts per bin).
  5. Label leakage prevention: risk_score used for labels ONLY, not as a feature.
  6. Two cleaning paths: full NLTK preprocess for model text; strip_markup
     only for keyword scoring (preserves phrases like "going concern").
  7. Min 30 words filter: drops filings too sparse after cleaning.
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
# Keyword lexicons for weak-supervision risk scoring
#
# Interview tip: these are domain-informed, not learned. Trade-off: interpretable
# and fast, but miss nuanced risks and may overfit to exact phrase matching.
# High-risk terms weighted 3× because they signal existential/legal danger.
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

# Singleton NLTK preprocessor — shared across all clean_text() calls
_preprocessor = get_preprocessor()


# ---------------------------------------------------------------------------
# Text cleaning — delegates to NLTK TextPreprocessor
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """
    Normalise raw filing text for model consumption.

    Full NLP pipeline (via TextPreprocessor):
      1. strip_markup  — HTML tags, entities, SEC boilerplate (regex)
      2. tokenize      — NLTK word_tokenize
      3. filter_tokens — remove stop words, short/noise tokens
      4. lemmatize     — WordNet lemmatization (losses → loss)
      5. rejoin        — single space-separated string for TF-IDF

    Args:
        text: Raw section text from Hugging Face dataset.

    Returns:
        Cleaned, lowercased, lemmatized string.
    """
    return _preprocessor.preprocess(text)


# ---------------------------------------------------------------------------
# Section extraction — map dataset columns to logical 10-K sections
# ---------------------------------------------------------------------------
def extract_sections(row: dict) -> dict[str, str]:
    """
    Pull the four key 10-K sections from one raw dataset record.

    Each section is cleaned independently so features.py can compute
    per-section word counts (custom features) later.

    Section mapping defined in utils.SECTION_COLUMNS:
      business, risk_factors, mda, financial_statements

    Args:
        row: Single dict from Hugging Face parquet (one company filing).

    Returns:
        Dict mapping section key → cleaned text string.
    """
    sections: dict[str, str] = {}
    for key, column in SECTION_COLUMNS.items():
        raw = row.get(column) or ""
        sections[key] = clean_text(str(raw))
    return sections


def build_document_text(sections: dict[str, str]) -> str:
    """
    Concatenate all sections into one document string for TF-IDF.

    Risk Factors is placed FIRST because it carries the strongest risk signal
    in 10-K filings (Item 1A). Order matters slightly for n-gram context at
    document boundaries.

    Args:
        sections: Output of extract_sections().

    Returns:
        Single space-joined string of non-empty sections.
    """
    ordered = ("risk_factors", "business", "mda", "financial_statements")
    parts = [sections[name] for name in ordered if sections.get(name)]
    return " ".join(parts).strip()


# ---------------------------------------------------------------------------
# Weak-supervision labeling — keyword density scoring
# ---------------------------------------------------------------------------
def compute_risk_score(risk_text: str) -> float:
    """
    Score how risky a filing's Risk Factors section sounds via keyword density.

    Formula:
      score = (high_hits × 3 + medium_hits × 1) / word_count × 1000

    Multiplying by 1000 scales scores to a readable numeric range.
    Substring matching (term in text) — simple but misses negation/context.

    Args:
        risk_text: Markup-stripped (NOT fully lemmatized) Risk Factors text.
                   strip_markup preserves multi-word phrases for matching.

    Returns:
        Non-negative float risk score.
    """
    if not risk_text:
        return 0.0

    text = risk_text.lower()
    words = max(len(text.split()), 1)
    high_hits = sum(3.0 for term in HIGH_RISK_TERMS if term in text)
    medium_hits = sum(1.0 for term in MEDIUM_RISK_TERMS if term in text)
    density = (high_hits + medium_hits) / words
    return float(density * 1000.0)


def assign_risk_labels(scores: list[float]) -> list[str]:
    """
    Convert numeric risk scores into low / medium / high categorical labels.

    Primary method: pd.qcut on ranks → three equal-sized groups (terciles).
      - Bottom third  → "low"
      - Middle third  → "medium"
      - Top third     → "high"

    Fallback: if qcut fails (too few unique scores), median split → high/low only.

    Interview Q: "Why quantile bins?" — Ensures balanced classes for training;
    absolute score thresholds would depend on corpus-specific calibration.

    Args:
        scores: List of compute_risk_score() values, one per filing.

    Returns:
        Parallel list of "low", "medium", or "high" strings.
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


# ---------------------------------------------------------------------------
# Data loading — Hugging Face Hub parquet download
# ---------------------------------------------------------------------------
def load_raw_records(max_samples: int = DEFAULT_MAX_SAMPLES) -> list[dict]:
    """
    Download SEC filings parquet from Hugging Face Hub and load into memory.

    Uses hf_hub_download for caching — subsequent runs reuse local cache.
    Dataset: winterForestStump/10-K_sec_filings, split 026 parquet shard.

    Args:
        max_samples: Cap on number of filings to load (head of dataframe).

    Returns:
        List of row dicts, one per filing record.
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


# ---------------------------------------------------------------------------
# Main preprocessing orchestrator — called by run_pipeline.py
# ---------------------------------------------------------------------------
def preprocess_records(max_samples: int = DEFAULT_MAX_SAMPLES) -> pd.DataFrame:
    """
    Full preprocessing pipeline: load → clean → score → label → DataFrame.

    Per-record workflow:
      1. extract_sections() from raw Hugging Face columns
      2. build_document_text() for combined TF-IDF input
      3. Skip if <30 words after cleaning (unusable document)
      4. compute_risk_score() on strip_markup Risk Factors (not lemmatized)
      5. Collect all scores, then assign_risk_labels() globally (qcut needs full distribution)

    Output columns:
      company_name, filing_date, text, risk_score, risk_label,
      section_risk_factors, section_business, section_mda, section_financials

    Args:
        max_samples: Passed to load_raw_records().

    Returns:
        pandas DataFrame with one row per usable filing.

    Raises:
        ValueError: If no records survive the 30-word filter.
    """
    rows: list[dict] = []
    risk_scores: list[float] = []

    for record in load_raw_records(max_samples=max_samples):
        sections = extract_sections(record)
        document_text = build_document_text(sections)

        # Quality gate — filings too short after cleaning add noise, not signal
        if len(document_text.split()) < 30:
            continue

        # Keyword scoring uses markup-stripped text to preserve phrases like "going concern"
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

    # Labels assigned AFTER all scores collected — qcut needs full distribution
    labels = assign_risk_labels(risk_scores)
    frame = pd.DataFrame(rows)
    frame["risk_label"] = labels
    logger.info("Prepared %s records with label distribution:\n%s", len(frame), frame["risk_label"].value_counts())
    return frame


def save_processed(frame: pd.DataFrame, path) -> None:
    """
    Persist processed DataFrame to CSV for inspection and reproducibility.

    Args:
        frame: Output of preprocess_records().
        path: Target CSV path (typically data/processed_filings.csv).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    logger.info("Saved processed data to %s", path)
