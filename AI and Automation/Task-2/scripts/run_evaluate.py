#!/usr/bin/env python
"""
=============================================================================
Stage 4 CLI Wrapper — RAG Pipeline Evaluation
=============================================================================

PURPOSE
-------
Thin entry-point script that invokes src/evaluate.py's main() to benchmark
multiple RAG pipeline configurations and select the best performer.

ROLE IN THE RAG PIPELINE
------------------------
  Stage 4 of 5: Pipeline Evaluation & Selection

  Input:  data/eval_questions.json (gold Q&A with expected keywords)
          models/vector_store/     (must exist from Stage 2)
          Ollama running locally   (for generative pipeline modes)

  Output: reports/evaluation_report.json  (per-question details)
          reports/metrics_comparison.csv  (pipeline summary table)
          reports/metrics_comparison.png  (bar chart visualization)
          recommended_pipeline in report  (consumed by run_pipeline.py)

  Metrics (interview acronym cheat sheet):
    CR — Context Relevance:  did retrieval find the right chunks?
    F  — Faithfulness:       is the answer grounded in retrieved text?
    AR — Answer Relevance:   does the answer address the question?
    L  — Latency (ms):       end-to-end response time
    QR — Query Resolution:   answer contains expected keywords (task success)

INTERVIEW TALKING POINTS
------------------------
1. **Why evaluate three paths?** extractive = retrieval baseline (no LLM cost);
   local_llm = pure vector+LLM; reranked_local = precision boost via cross-encoder.
2. **Winner selection:** max QR, then F, then min latency — prioritizes
   correct answers over speed, with faithfulness as tiebreaker.
3. **Embedding-based metrics:** CR/F/AR use same MiniLM model as retrieval —
   consistent semantic space, no extra API calls.
4. **Automated recommendation:** evaluation output drives deployment config
   (pipeline_state.json) — closes the build→measure→deploy loop.

USAGE:
    python scripts/run_evaluate.py
    python scripts/run_evaluate.py --pipelines reranked_local extractive

PREREQUISITES:
    python scripts/run_ingest.py && python scripts/run_embed.py
    ollama pull qwen2.5:7b && ollama serve
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.evaluate import main

if __name__ == "__main__":
    main()
