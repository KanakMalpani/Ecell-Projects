#!/usr/bin/env python
"""End-to-end pipeline runner for all five stages."""

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

    logger.info("=== Stage 1: Ingestion & Segmentation ===")
    ingest_corpus(raw_dir, processed_dir)

    logger.info("=== Stage 2: Embedding & Indexing ===")
    build_index()

    if not args.skip_eval:
        logger.info("=== Stage 4: Evaluation ===")
        report = run_evaluation(pipelines=args.pipelines)
        recommended = report["recommended_pipeline"]
    else:
        recommended = config["evaluation"]["default_pipeline"]

    logger.info("=== Stage 5: Saving system state ===")
    save_pipeline_state(recommended)  # type: ignore[arg-type]
    state_dir = resolve_path(config["paths"]["state_dir"])
    with (state_dir / "pipeline_state.json").open(encoding="utf-8") as handle:
        state = json.load(handle)
    logger.info("Active pipeline saved: %s", state.get("active_pipeline"))
    logger.info("Done. Start API: uvicorn api.app:app --reload")


if __name__ == "__main__":
    main()
