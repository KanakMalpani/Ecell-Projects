#!/usr/bin/env python
"""
End-to-end pipeline runner for all five RAG stages.

Task 2 builds a Retrieval-Augmented Generation (RAG) system:
  ask a question → search company documents → LLM answers from context only.

Stages:
  1. Ingest   — read PDFs/txt, split into chunks          (src/ingest.py)
  2. Embed    — turn chunks into vectors, store in ChromaDB (src/embed.py)
  3. Orchestrate — retrieve + rerank + LLM answer         (src/orchestrate.py)
  4. Evaluate — benchmark 3 pipeline paths                 (src/evaluate.py)
  5. Deploy   — FastAPI /query endpoint                    (api/app.py)

Usage:
    python run_pipeline.py
    python run_pipeline.py --skip-eval
    python run_pipeline.py --pipelines local_llm reranked_local extractive
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

    # Stage 1: read documents from data/raw/, save chunks to data/processed/chunks.json
    logger.info("=== Stage 1: Ingestion & Segmentation ===")
    ingest_corpus(raw_dir, processed_dir)

    # Stage 2: embed chunks and build ChromaDB vector index
    logger.info("=== Stage 2: Embedding & Indexing ===")
    build_index()

    if not args.skip_eval:
        # Stage 4: run eval questions through each pipeline, pick the best
        logger.info("=== Stage 4: Evaluation ===")
        report = run_evaluation(pipelines=args.pipelines)
        recommended = report["recommended_pipeline"]
    else:
        recommended = config["evaluation"]["default_pipeline"]

    # Save which pipeline mode the API should use (e.g. reranked_local)
    logger.info("=== Stage 5: Saving system state ===")
    save_pipeline_state(recommended)  # type: ignore[arg-type]
    state_dir = resolve_path(config["paths"]["state_dir"])
    with (state_dir / "pipeline_state.json").open(encoding="utf-8") as handle:
        state = json.load(handle)
    logger.info("Active pipeline saved: %s", state.get("active_pipeline"))
    logger.info("Done. Start API: uvicorn api.app:app --reload")


if __name__ == "__main__":
    main()
