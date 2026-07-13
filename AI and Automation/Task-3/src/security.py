"""
Safe path helpers for report file downloads.

WHAT THIS FILE DOES
-------------------
Validates report filenames before serving them via GET /api/v1/reports/{filename}
to prevent path traversal attacks (e.g. ../../../etc/passwd).

SECURITY CHECKS (safe_report_path)
----------------------------------
  1. Filename must match regex ^[A-Za-z0-9._-]+$ (no slashes or dots-only)
  2. Resolved absolute path must stay inside reports/ directory
  3. File must actually exist (404 if not)

PI INTERVIEW TALKING POINTS
---------------------------
  Q: What is path traversal?
  A: Attacker requests /api/v1/reports/../../.env to read sensitive files.
     safe_report_path() resolves the path and verifies parent == reports_dir.

  Q: Why regex on filename instead of just path resolution?
  A: Defense in depth — reject malicious filenames before any filesystem access.
"""

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
