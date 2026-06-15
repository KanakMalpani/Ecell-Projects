#!/usr/bin/env python
"""
Run Stage 1 only: document ingestion and chunking.

Equivalent to the first step of run_pipeline.py.
Reads PDFs/txt from data/raw/, saves chunks to data/processed/chunks.json.

Usage: python scripts/run_ingest.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingest import main

if __name__ == "__main__":
    main()
