"""Stage 1: load 10-K filings, clean text, extract sections, derive risk labels."""

from __future__ import annotations

import re

import pandas as pd
from huggingface_hub import hf_hub_download

from .utils import (
    DATASET_NAME,
    DATASET_SPLIT,
    DATASET_SPLIT_FILE,
    DEFAULT_MAX_SAMPLES,
    SECTION_COLUMNS,
    setup_logging,
)

logger = setup_logging(__name__)

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

BOILERPLATE_PATTERNS = (
    r"table of contents",
    r"forward[- ]looking statements",
    r"item\s+\d+[a-z]?\.?",
    r"page\s+\d+\s+of\s+\d+",
    r"sec\.gov",
    r"united states securities and exchange commission",
)

NOISE_PATTERN = re.compile(r"[^a-z0-9\s\.\,\;\:\-\%\$\(\)]+", re.IGNORECASE)
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    cleaned = text.lower()
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = re.sub(r"&#\d+;", " ", cleaned)
    cleaned = NOISE_PATTERN.sub(" ", cleaned)

    for pattern in BOILERPLATE_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    cleaned = WHITESPACE_PATTERN.sub(" ", cleaned).strip()
    return cleaned


def extract_sections(row: dict) -> dict[str, str]:
    sections: dict[str, str] = {}
    for key, column in SECTION_COLUMNS.items():
        raw = row.get(column) or ""
        sections[key] = clean_text(str(raw))
    return sections


def build_document_text(sections: dict[str, str]) -> str:
    ordered = ("risk_factors", "business", "mda", "financial_statements")
    parts = [sections[name] for name in ordered if sections.get(name)]
    return " ".join(parts).strip()


def compute_risk_score(risk_text: str) -> float:
    if not risk_text:
        return 0.0

    text = risk_text.lower()
    words = max(len(text.split()), 1)
    high_hits = sum(3.0 for term in HIGH_RISK_TERMS if term in text)
    medium_hits = sum(1.0 for term in MEDIUM_RISK_TERMS if term in text)
    density = (high_hits + medium_hits) / words
    return float(density * 1000.0)


def assign_risk_labels(scores: list[float]) -> list[str]:
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
    rows: list[dict] = []
    risk_scores: list[float] = []

    for record in load_raw_records(max_samples=max_samples):
        sections = extract_sections(record)
        document_text = build_document_text(sections)
        if len(document_text.split()) < 30:
            continue

        risk_score = compute_risk_score(sections.get("risk_factors", ""))
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

    labels = assign_risk_labels(risk_scores)
    frame = pd.DataFrame(rows)
    frame["risk_label"] = labels
    logger.info("Prepared %s records with label distribution:\n%s", len(frame), frame["risk_label"].value_counts())
    return frame


def save_processed(frame: pd.DataFrame, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    logger.info("Saved processed data to %s", path)
