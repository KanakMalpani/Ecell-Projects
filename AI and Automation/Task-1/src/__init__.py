"""
10-K SEC filing risk classification pipeline — core ML package.

WHAT THIS PACKAGE DOES
----------------------
Contains all reusable machine-learning logic for Task 1: loading and cleaning
SEC 10-K filings, engineering features, training classifiers, and evaluating
them. The API (api/app.py) and orchestrator (run_pipeline.py) import from here.

WHY IT EXISTS
-------------
Keeps the project modular. Each module owns one pipeline stage so you can
explain, test, or swap components independently during an interview.

MODULE MAP (execution order)
----------------------------
  preprocess.py       Stage 1 — data ingestion, NLP cleaning, label creation
  text_preprocessor.py  Helper — NLTK tokenization, stop words, lemmatization
  features.py         Stage 2 — TF-IDF vectorization + custom numeric features
  train.py            Stage 3 — XGBoost, AdaBoost, CatBoost training
  evaluate.py         Stage 4 — metrics, confusion matrices, model selection
  utils.py            Shared — paths, dataset config, logging, constants

HOW IT FITS IN THE PIPELINE
--------------------------
  run_pipeline.py imports preprocess → features → evaluate (which calls train)
  api/app.py imports features, preprocess, train (for TrainedModel type only)

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Package as bounded context: everything under src/ is "ML core";
     api/ is "serving"; video script is "presentation".
  2. Weak supervision: labels are derived from keyword scoring, not human
     annotation — important limitation to acknowledge.
  3. Text → numbers → ensemble classifiers → 3-way risk prediction.
  4. Artifacts (joblib) bridge offline training and online inference.
"""
