#!/usr/bin/env python
"""Run Stage 1: document ingestion and chunking."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingest import main

if __name__ == "__main__":
    main()
