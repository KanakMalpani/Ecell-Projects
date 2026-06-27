"""Safe path helpers for report downloads."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import HTTPException

_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9._-]+$")


def safe_report_path(reports_dir: Path, filename: str) -> Path:
    """Resolve a report file and block path traversal."""
    if not filename or not _SAFE_FILENAME.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    base = reports_dir.resolve()
    path = (base / filename).resolve()
    if path.parent != base:
        raise HTTPException(status_code=403, detail="Access denied")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Report not found")
    return path
