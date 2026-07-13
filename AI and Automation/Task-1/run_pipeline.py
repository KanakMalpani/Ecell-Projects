"""
Run the full 10-K classification pipeline end to end.

WHAT THIS FILE DOES
-------------------
Orchestrates all offline ML stages in sequence: preprocess → features →
train → evaluate. One command produces everything the API needs.

WHY IT EXISTS
-------------
Splitting logic across src/ modules keeps each stage testable and readable,
but users need a single entry point. This script is the "make" command for
the project — run it once before starting the API.

HOW IT FITS IN THE PIPELINE
---------------------------
  Stage 1  preprocess.py   → data/processed_filings.csv
  Stage 2  features.py      → models/tfidf_vectorizer.joblib + feature matrix
  Stage 3  train.py         → (inside evaluate) fits XGBoost, AdaBoost, CatBoost
  Stage 4  evaluate.py      → reports/* + models/best_model.joblib + label_map
  Stage 5  api/app.py       → manual: uvicorn api.app:app --reload

Data flow:
  HuggingFace parquet → DataFrame → sparse feature matrix → trained models
  → evaluation report → best model artifact

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Pipeline orchestration vs modular stages — separation of concerns.
  2. --max-samples flag for fast iteration during development (500 default).
  3. Labels flow separately from features (list of strings, not in matrix).
  4. Idempotency: re-running overwrites artifacts — no incremental training.
  5. Stage 5 is intentionally manual to decouple long training from serving.

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
    """
    Execute all four offline pipeline stages in order.

    Steps:
        1. Parse CLI args (--max-samples controls HuggingFace download size)
        2. Create output directories (data/, models/, reports/)
        3. Preprocess filings and save CSV
        4. Fit TF-IDF + build feature matrix, persist vectorizer
        5. Train 3 models, evaluate on hold-out set, save best model

    Interview tip: features are fit on ALL preprocessed rows before the
    train/test split inside run_evaluation(). In production you might fit
    TF-IDF only on training data to avoid leakage — here the dataset is
    small and the vectorizer vocabulary is document-level, not label-level.
    """
    # --- CLI configuration ---
    parser = argparse.ArgumentParser(description="Run 10-K risk classification pipeline")
    parser.add_argument("--max-samples", type=int, default=500, help="Maximum filings to load")
    args = parser.parse_args()

    ensure_dirs()
    logger.info("Starting pipeline with max_samples=%s", args.max_samples)

    # --- Stage 1: Preprocess ---
    # Downloads SEC filings from Hugging Face, cleans text via NLTK,
    # extracts four 10-K sections, scores Risk Factors with keywords,
    # assigns low/medium/high labels via quantile bucketing (pd.qcut).
    frame = preprocess_records(max_samples=args.max_samples)
    save_processed(frame, DATA_DIR / "processed_filings.csv")

    # --- Stage 2: Feature engineering ---
    # Converts each document's cleaned text into a sparse matrix:
    # 5000 TF-IDF columns + 6 custom numeric features = 5006 total.
    # Saves fitted TfidfVectorizer for API inference consistency.
    features, artifacts = fit_features(frame)
    save_feature_artifacts(artifacts)

    # --- Stages 3 + 4: Train, evaluate, persist winner ---
    # run_evaluation() performs 80/20 stratified split, trains all models
    # on train set, scores on test set, picks best by macro F1.
    labels = frame["risk_label"].tolist()
    report, best_model, _ = run_evaluation(features, labels)

    logger.info("Pipeline complete. Best model: %s", best_model)
    logger.info("Reports saved under %s", REPORTS_DIR)
    logger.info("Start API with: uvicorn api.app:app --reload")


if __name__ == "__main__":
    main()
