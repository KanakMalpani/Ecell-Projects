#!/usr/bin/env python
"""Run Stage 2: embedding generation and vector indexing."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embed import main

if __name__ == "__main__":
    main()
