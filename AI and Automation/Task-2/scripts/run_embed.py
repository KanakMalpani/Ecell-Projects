#!/usr/bin/env python
"""
=============================================================================
Stage 2 CLI Wrapper — Embedding & Vector Indexing
=============================================================================

PURPOSE
-------
Thin entry-point script that invokes src/embed.py's main() so Stage 2 can be
run independently without executing the full five-stage pipeline.

ROLE IN THE RAG PIPELINE
------------------------
  Stage 2 of 5: Embedding Generation & Vector Indexing

  Input:  data/processed/chunks.json  (from Stage 1 ingest)
  Output: models/vector_store/        (ChromaDB persistent collection)
          models/state/index_state.json (index metadata/stats)

  At query time (Stage 3), the user's question is embedded with the SAME model
  and ChromaDB returns nearest-neighbor chunks by cosine distance.

INTERVIEW TALKING POINTS
------------------------
1. **Why a separate script?** Modular stages enable debugging — if retrieval
   is poor, re-embed without re-ingesting. Faster iteration loop.
2. **--no-reset flag:** Append mode for incremental doc adds (advanced); default
   wipes and rebuilds for reproducible demos.
3. **normalize_embeddings=True:** Unit-length vectors make cosine distance
   equivalent to dot product — standard practice for semantic search.
4. **ChromaDB PersistentClient:** Index survives process restarts; no separate
   vector DB server needed for this enterprise POC.

USAGE:
    python scripts/run_embed.py
    python scripts/run_embed.py --no-reset   # append without wiping index

PREREQUISITE:
    python scripts/run_ingest.py   # Stage 1 must produce chunks.json first
"""

import sys
from pathlib import Path

# Add project root to sys.path so `from src.*` imports resolve
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.embed import main

if __name__ == "__main__":
    main()
