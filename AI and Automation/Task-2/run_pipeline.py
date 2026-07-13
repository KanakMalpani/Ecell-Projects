#!/usr/bin/env python
"""
=============================================================================
End-to-End RAG Pipeline Runner (Stages 1–4 + State Save for Stage 5)
=============================================================================

PURPOSE
-------
Single entry point that orchestrates the full Enterprise RAG build pipeline:
ingest documents → embed chunks → evaluate pipeline variants → persist the
winning configuration for the FastAPI deployment layer.

ROLE IN THE RAG PIPELINE
------------------------
This script is the "conductor" — it does not implement RAG logic itself but
sequences the four core modules in the correct dependency order:

  Stage 1  src/ingest.py      → data/processed/chunks.json
  Stage 2  src/embed.py       → models/vector_store/ (ChromaDB)
  Stage 4  src/evaluate.py    → reports/ + recommended_pipeline
  Stage 5  save_pipeline_state → models/state/pipeline_state.json
           (api/app.py reads this on startup)

Note: Stage 3 (orchestrate) runs inside evaluation and at API query time;
it is not a separate batch step here.

INTERVIEW TALKING POINTS
------------------------
1. **Pipeline as DAG:** Stages have hard dependencies — embed needs chunks,
   evaluate needs index, API needs state. This script encodes that order.
2. **--skip-eval flag:** Useful for fast iteration on ingest/embed only;
   falls back to evaluation.default_pipeline from settings.yaml.
3. **--pipelines flag:** Benchmarks local_llm, reranked_local, extractive —
   demonstrates understanding of retrieval-only vs. generative vs. reranked paths.
4. **Evaluation-driven deployment:** The "best" pipeline is data-driven (QR, F,
   latency), not hardcoded — shows MLOps/eval mindset.
5. **sys.path.insert:** Adds project root so `from src.*` works when run as
   `python run_pipeline.py` from any cwd within the project.

USAGE:
    python run_pipeline.py
    python run_pipeline.py --skip-eval
    python run_pipeline.py --pipelines local_llm reranked_local extractive

AFTER COMPLETION:
    uvicorn api.app:app --reload   # Stage 5 — start the REST API
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.embed import build_index
from src.evaluate import run_evaluation
from src.ingest import ingest_corpus
from src.orchestrate import save_pipeline_state
from src.utils import load_config, resolve_path, setup_logging

logger = setup_logging("pipeline")


def main() -> None:
    """
    CLI entry: parse args, run stages sequentially, save active pipeline state.

    Interview note: Each stage logs a clear banner (=== Stage N ===) so demo
    videos and CI logs show progress. Failures in any stage propagate up and
    exit non-zero (standard Python exception behavior).
    """
    parser = argparse.ArgumentParser(description="Run full RAG pipeline (stages 1-4)")
    parser.add_argument("--skip-eval", action="store_true", help="Skip evaluation stage")
    parser.add_argument(
        "--pipelines",
        nargs="+",
        default=["local_llm", "reranked_local", "extractive"],
        help="Pipelines to benchmark",
    )
    args = parser.parse_args()

    config = load_config()
    raw_dir = resolve_path(config["paths"]["raw_dir"])
    processed_dir = resolve_path(config["paths"]["processed_dir"])

    # -------------------------------------------------------------------------
    # Stage 1: Document Ingestion & Segmentation
    # -------------------------------------------------------------------------
    # Reads PDF/txt/md from data/raw/, outputs data/processed/chunks.json
    logger.info("=== Stage 1: Ingestion & Segmentation ===")
    ingest_corpus(raw_dir, processed_dir)

    # -------------------------------------------------------------------------
    # Stage 2: Embedding Generation & Vector Indexing
    # -------------------------------------------------------------------------
    # Encodes chunks with sentence-transformers, persists to ChromaDB
    logger.info("=== Stage 2: Embedding & Indexing ===")
    build_index()

    # -------------------------------------------------------------------------
    # Stage 4: Pipeline Evaluation (optional)
    # -------------------------------------------------------------------------
    # Runs eval_questions.json through each pipeline mode; picks winner by QR/F/L
    if not args.skip_eval:
        logger.info("=== Stage 4: Evaluation ===")
        report = run_evaluation(pipelines=args.pipelines)
        recommended = report["recommended_pipeline"]
    else:
        recommended = config["evaluation"]["default_pipeline"]

    # -------------------------------------------------------------------------
    # Stage 5 prep: Persist winning pipeline for API bootstrap
    # -------------------------------------------------------------------------
    # api/app.py reads pipeline_state.json to set ACTIVE_MODE at import time
    logger.info("=== Stage 5: Saving system state ===")
    save_pipeline_state(recommended)  # type: ignore[arg-type]
    state_dir = resolve_path(config["paths"]["state_dir"])
    with (state_dir / "pipeline_state.json").open(encoding="utf-8") as handle:
        state = json.load(handle)
    logger.info("Active pipeline saved: %s", state.get("active_pipeline"))
    logger.info("Done. Start API: uvicorn api.app:app --reload")


if __name__ == "__main__":
    main()
