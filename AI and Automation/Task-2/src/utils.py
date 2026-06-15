"""
Shared utilities for the RAG knowledge management pipeline.

Central place for:
  - Project paths and config loading (settings.yaml)
  - Text cleaning helpers
  - JSON read/write helpers
  - Document type detection
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "settings.yaml"


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure timestamped logging for any pipeline module."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


def load_config() -> dict[str, Any]:
    """Load all settings from config/settings.yaml (chunk sizes, models, paths)."""
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_path(relative: str, *, mkdir: bool = True) -> Path:
    """
    Turn a config-relative path like 'data/raw' into an absolute Path.

    Automatically creates the folder if mkdir=True.
    """
    path = PROJECT_ROOT / relative
    if mkdir and not path.suffix:
        path.mkdir(parents=True, exist_ok=True)
    elif mkdir and path.parent != path:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_json(path: Path, payload: Any) -> None:
    """Write any Python object to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Any:
    """Read a JSON file and return the parsed Python object."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# Regex patterns for structural boilerplate lines in enterprise PDFs
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

    Documents keep full vocabulary for embedding quality — only structural
    boilerplate is stripped here. Stop-word removal runs on queries via
    TextPreprocessor in orchestrate.py.
    """
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    for pattern in HEADER_FOOTER_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = MULTISPACE_PATTERN.sub(" ", cleaned)
    cleaned = WHITESPACE_PATTERN.sub("\n\n", cleaned)
    return cleaned.strip()


def detect_document_type(filename: str, content: str) -> str:
    """
    Classify a document by filename and opening text.

    Used as metadata tags stored with each chunk in the vector index.
    Returns one of: standard_operating_procedure, corporate_policy,
    compliance_regulation, technical_troubleshooting_log, general_document
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
