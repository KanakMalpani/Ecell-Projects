"""
=============================================================================
Shared Utilities — Config, Paths, I/O, Text Cleaning
=============================================================================

PURPOSE
-------
Central infrastructure module used by every stage of the RAG pipeline.
Eliminates duplicated path resolution, config loading, and text-cleaning logic.

ROLE IN THE RAG PIPELINE
------------------------
  Consumed by: ingest.py, embed.py, orchestrate.py, evaluate.py, api/app.py

  Key responsibilities:
    - load_config()     → read config/settings.yaml (single source of truth)
    - resolve_path()    → project-root-relative paths with auto-mkdir
    - save_json/load_json → pipeline artifact I/O (chunks, state, reports)
    - clean_text()      → document-side boilerplate removal (Stage 1)
    - detect_document_type() → chunk metadata classification (Stage 1)
    - setup_logging()   → consistent timestamped log format

INTERVIEW TALKING POINTS
------------------------
1. **PROJECT_ROOT derivation:** Path(__file__).parents[1] — works regardless of
   which script is the entry point (run_pipeline.py, scripts/*, uvicorn).
2. **YAML config centralization:** All tunables in settings.yaml; Python code
   reads via load_config() — ops-friendly, no magic numbers in source.
3. **resolve_path mkdir=True:** Auto-creates data/, models/, reports/ dirs on
   first access — reduces setup friction for demos and CI.
4. **clean_text vs TextPreprocessor:** clean_text() strips structural boilerplate
   from DOCUMENTS at ingest time; TextPreprocessor handles QUERY normalization
   at retrieval time — intentional asymmetry for embedding quality.
5. **detect_document_type heuristics:** Filename + first-200-chars content scan;
   lightweight metadata tag for UI badges and future filtered retrieval.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

# -----------------------------------------------------------------------------
# Project constants — anchor all relative paths to Task-2 root
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


# -----------------------------------------------------------------------------
# Logging setup — shared format across all pipeline modules
# -----------------------------------------------------------------------------
def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure timestamped logging for any pipeline module.

    Format: 2024-01-15 10:30:00 | INFO | ingest | Found 7 source documents
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


# -----------------------------------------------------------------------------
# Configuration loading
# -----------------------------------------------------------------------------
def load_config() -> dict[str, Any]:
    """
    Load all pipeline settings from config/settings.yaml.

    Returns nested dict with keys: paths, chunking, embedding, retrieval,
    llm, evaluation, anti_hallucination, preprocessing.
    """
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


# -----------------------------------------------------------------------------
# Path resolution — config-relative → absolute with optional mkdir
# -----------------------------------------------------------------------------
def resolve_path(relative: str, *, mkdir: bool = True) -> Path:
    """
    Turn a config-relative path like 'data/raw' into an absolute Path.

    Automatically creates the directory (or parent for file paths) if mkdir=True.
    Interview: enables "drop files and run" workflow without manual mkdir steps.
    """
    path = PROJECT_ROOT / relative
    if mkdir and not path.suffix:
        path.mkdir(parents=True, exist_ok=True)
    elif mkdir and path.parent != path:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


# -----------------------------------------------------------------------------
# JSON I/O helpers — pipeline artifacts (chunks, state, reports)
# -----------------------------------------------------------------------------
def save_json(path: Path, payload: Any) -> None:
    """Write any JSON-serializable Python object to disk with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Any:
    """Read and parse a JSON file — used for chunks.json, eval questions, state files."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# -----------------------------------------------------------------------------
# Document text cleaning — structural boilerplate removal (Stage 1)
# -----------------------------------------------------------------------------
# Regex patterns for enterprise PDF headers/footers — shared with text_preprocessor
HEADER_FOOTER_PATTERNS = [
    re.compile(r"^Page \d+ of \d+\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^Confidential\s*[-|]\s*Internal Use Only\s*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Document ID:.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Version \d+\.\d+.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Effective:.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Last Updated:.*$", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^\s*Owner:.*$", re.MULTILINE | re.IGNORECASE),
]

WHITESPACE_PATTERN = re.compile(r"\n{3,}")
MULTISPACE_PATTERN = re.compile(r"[ \t]{2,}")


def clean_text(text: str) -> str:
    """
    Remove headers, footers, and layout noise from raw document text.

    Applied at INGEST time on full documents — preserves vocabulary for embedding.
    Stop-word removal is deferred to query-side TextPreprocessor in orchestrate.py.

    Interview: only structural noise removed; semantic content kept intact.
    """
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    for pattern in HEADER_FOOTER_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = MULTISPACE_PATTERN.sub(" ", cleaned)
    cleaned = WHITESPACE_PATTERN.sub("\n\n", cleaned)
    return cleaned.strip()


# -----------------------------------------------------------------------------
# Document type classification — chunk metadata (Stage 1)
# -----------------------------------------------------------------------------
def detect_document_type(filename: str, content: str) -> str:
    """
    Classify a document by filename and opening text content.

    Heuristic rules tuned for enterprise corpus (SOPs, policies, compliance).
    Returned value stored as doc_type metadata on each chunk in ChromaDB.

    Possible values:
      standard_operating_procedure, corporate_policy, compliance_regulation,
      technical_troubleshooting_log, general_document
    """
    name = filename.lower()
    if "sop" in name or "standard operating" in content.lower()[:200]:
        return "standard_operating_procedure"
    if "policy" in name or "policy framework" in content.lower()[:200]:
        return "corporate_policy"
    if "compliance" in name or "gdpr" in name or "regulation" in content.lower()[:200]:
        return "compliance_regulation"
    if "troubleshoot" in name or "log" in name:
        return "technical_troubleshooting_log"
    return "general_document"
