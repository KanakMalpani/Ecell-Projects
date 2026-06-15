#!/usr/bin/env python
"""
Run Stage 4 only: pipeline evaluation.

Runs eval questions through each pipeline mode, saves metrics to reports/.

Usage: python scripts/run_evaluate.py
       python scripts/run_evaluate.py --pipelines reranked_local extractive
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluate import main

if __name__ == "__main__":
    main()
