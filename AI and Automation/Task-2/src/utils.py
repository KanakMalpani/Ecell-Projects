"""Shared utilities for the RAG knowledge management pipeline."""

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
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def resolve_path(relative: str, *, mkdir: bool = True) -> Path:
    path = PROJECT_ROOT / relative
    if mkdir and not path.suffix:
        path.mkdir(parents=True, exist_ok=True)
    elif mkdir and path.parent != path:
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


# Patterns for boilerplate / layout noise removal
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
    """Remove headers, footers, boilerplate, and layout noise."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    for pattern in HEADER_FOOTER_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = MULTISPACE_PATTERN.sub(" ", cleaned)
    cleaned = WHITESPACE_PATTERN.sub("\n\n", cleaned)
    return cleaned.strip()


def detect_document_type(filename: str, content: str) -> str:
    """Classify document structure for metadata tagging."""
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
