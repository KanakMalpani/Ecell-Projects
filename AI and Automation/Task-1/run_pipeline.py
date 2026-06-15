"""
Run the full 10-K classification pipeline end to end.

This is the MAIN entry point. One command runs all five stages:

  Stage 1  preprocess  → download filings, clean text, create labels
  Stage 2  features    → convert text to TF-IDF numeric vectors
  Stage 3  train       → fit XGBoost, AdaBoost, CatBoost
  Stage 4  evaluate    → test models, pick the best, save reports
  Stage 5  (manual)    → start the API with: uvicorn api.app:app --reload

Usage:
    python run_pipeline.py
    python run_pipeline.py --max-samples 800
"""

from __future__ import annotations

import argparse

from src.evaluate import run_evaluation
from src.features import fit_features, save_feature_artifacts
from src.preprocess import preprocess_records, save_processed
from src.utils import DATA_DIR, REPORTS_DIR, ensure_dirs, setup_logging

logger = setup_logging("pipeline")


def main() -> None:
    # Allow the user to limit how many filings to download (faster for testing)
    parser = argparse.ArgumentParser(description="Run 10-K risk classification pipeline")
    parser.add_argument("--max-samples", type=int, default=500, help="Maximum filings to load")
    args = parser.parse_args()

    ensure_dirs()
    logger.info("Starting pipeline with max_samples=%s", args.max_samples)

    # --- Stage 1: Preprocess ---
    # Downloads SEC filings, cleans text, creates low/medium/high labels
    frame = preprocess_records(max_samples=args.max_samples)
    save_processed(frame, DATA_DIR / "processed_filings.csv")

    # --- Stage 2: Feature engineering ---
    # Turns each document's text into a matrix of 5006 numbers (TF-IDF + custom)
    features, artifacts = fit_features(frame)
    save_feature_artifacts(artifacts)

    # --- Stages 3 + 4: Train, evaluate, save best model ---
    labels = frame["risk_label"].tolist()
    report, best_model, _ = run_evaluation(features, labels)

    logger.info("Pipeline complete. Best model: %s", best_model)
    logger.info("Reports saved under %s", REPORTS_DIR)
    logger.info("Start API with: uvicorn api.app:app --reload")


if __name__ == "__main__":
    main()
