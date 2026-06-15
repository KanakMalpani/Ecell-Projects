#!/usr/bin/env python
"""
Run Stage 2 only: embedding generation and vector indexing.

Reads data/processed/chunks.json, embeds with sentence-transformers,
stores vectors in ChromaDB at models/vector_store/.

Usage: python scripts/run_embed.py
       python scripts/run_embed.py --no-reset   # append without wiping index
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embed import main

if __name__ == "__main__":
    main()
