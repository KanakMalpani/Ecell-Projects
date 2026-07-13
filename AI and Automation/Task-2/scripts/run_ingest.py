#!/usr/bin/env python
"""
=============================================================================
Stage 1 CLI Wrapper — Document Ingestion & Chunking
=============================================================================

PURPOSE
-------
Thin entry-point script that invokes src/ingest.py's main() so Stage 1 can be
run in isolation — equivalent to the first step of run_pipeline.py.

ROLE IN THE RAG PIPELINE
------------------------
  Stage 1 of 5: Document Ingestion & Text Segmentation

  Input:  data/raw/*.pdf, *.txt, *.md  (enterprise SOPs, policies, compliance)
  Output: data/processed/chunks.json    (list of searchable text chunks)

  Each chunk carries metadata (source_file, doc_type, section_hint, token_count)
  that flows through embedding (Stage 2) and appears in API source citations.

INTERVIEW TALKING POINTS
------------------------
1. **Chunking strategy:** Section-aware split (headings) THEN token-based
   chunking with overlap — preserves semantic boundaries better than blind splits.
2. **tiktoken cl100k_base:** Same tokenizer family as GPT models — chunk_size
   in settings.yaml maps to real LLM context units.
3. **pdfplumber for PDFs:** Layout-aware text extraction vs. naive byte read;
   handles multi-page enterprise PDFs common in SOP libraries.
4. **doc_type metadata:** Heuristic classification (SOP, policy, compliance)
   enables filtered retrieval or UI badges in future extensions.
5. **Idempotent re-run:** Re-ingesting overwrites chunks.json — safe to add
   new files to raw_dir and re-run without manual cleanup.

USAGE:
    python scripts/run_ingest.py

NEXT STEP:
    python scripts/run_embed.py   # Stage 2 — embed chunks into ChromaDB
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingest import main

if __name__ == "__main__":
    main()
