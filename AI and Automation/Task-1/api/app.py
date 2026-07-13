"""
Stage 5: FastAPI deployment for the best trained model.

WHAT THIS FILE DOES
-------------------
Exposes the trained 10-K risk classifier as a REST API so anyone can send
filing text and receive a risk label (low / medium / high) plus a confidence
score. This is the production-serving layer of the pipeline.

WHY IT EXISTS
-------------
Training and evaluation happen offline in run_pipeline.py. Real users (or
demo judges) need a live endpoint — not a Jupyter notebook. FastAPI gives us:
  - Automatic OpenAPI/Swagger docs at /docs
  - Pydantic request validation (reject bad input early)
  - Async-ready architecture (though inference here is sync)

HOW IT FITS IN THE PIPELINE
---------------------------
  run_pipeline.py  →  saves models/best_model.joblib, label_map.joblib,
                        models/tfidf_vectorizer.joblib
  api/app.py       →  loads those artifacts ONCE at startup, reuses them
                        for every /predict request

  Request path mirrors training:
    raw text → clean_text() → build_document_text() → transform_features()
    → model.predict_proba() → argmax → label + confidence

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Cold start vs warm inference: model loaded at startup (not per request)
     to avoid disk I/O latency on every call.
  2. Training-serving skew: API must use the SAME preprocessing and TF-IDF
     vectorizer as training, or predictions will be meaningless.
  3. Sparse vs dense matrices: XGBoost accepts scipy sparse; AdaBoost/CatBoost
     need .toarray() — same logic as evaluate.py.
  4. Confidence = max(predict_proba), not a calibrated probability (worth
     mentioning if asked about model uncertainty).
  5. 503 Service Unavailable when artifacts missing — graceful degradation.

Usage:
    uvicorn api.app:app --reload
    → http://127.0.0.1:8000/docs

Endpoints:
    GET  /health   → {"status": "ok"}
    POST /predict  → {"label": "high", "confidence": 0.85}
"""

from __future__ import annotations

from pathlib import Path
import sys

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Project path setup — allow imports from src/ when uvicorn runs api/app.py
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features import load_feature_artifacts, transform_features
from src.preprocess import build_document_text, clean_text
from src.train import TrainedModel

MODELS_DIR = PROJECT_ROOT / "models"


# ---------------------------------------------------------------------------
# Request / Response schemas (Pydantic validates incoming JSON automatically)
#
# Interview note: Pydantic runs BEFORE the endpoint body executes. Invalid
# JSON (e.g. text shorter than 20 chars) returns 422 Unprocessable Entity.
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    """
    Schema for POST /predict body.

    Attributes:
        text: Raw 10-K filing text or a single section (min 20 chars to avoid
              trivial/empty inputs that would produce unreliable predictions).
    """

    text: str = Field(..., min_length=20, description="Raw 10-K filing text or section text")


class PredictResponse(BaseModel):
    """
    Schema for prediction output.

    Attributes:
        label: One of "low", "medium", or "high" — matches training labels.
        confidence: Probability assigned to the predicted class (0.0–1.0).
                    This is the max of predict_proba(), not a separate
                    calibration step.
    """

    label: str
    confidence: float


# ---------------------------------------------------------------------------
# FastAPI application instance and runtime globals
#
# Globals are populated once at startup and reused — classic singleton pattern
# for ML model serving (load heavy objects once, infer many times).
# ---------------------------------------------------------------------------
app = FastAPI(
    title="10-K Financial Risk Classifier",
    description="Classifies SEC 10-K filing text into low, medium, or high financial risk.",
    version="1.0.0",
)

_model: TrainedModel | None = None
_label_map: dict[int, str] | None = None
_feature_artifacts = None


def _load_runtime_assets() -> None:
    """
    Load trained model, integer→label map, and fitted TF-IDF vectorizer from disk.

    Called once at server startup. Raises FileNotFoundError if run_pipeline.py
    has not been executed yet (artifacts live under models/).

    Interview tip: joblib preserves sklearn/xgboost objects including fitted
    state — no need to re-fit at serve time.
    """
    global _model, _label_map, _feature_artifacts

    model_path = MODELS_DIR / "best_model.joblib"
    label_path = MODELS_DIR / "label_map.joblib"
    if not model_path.exists() or not label_path.exists():
        raise FileNotFoundError(
            "Trained model artifacts not found. Run `python run_pipeline.py` first."
        )

    _model = joblib.load(model_path)
    _label_map = joblib.load(label_path)
    _feature_artifacts = load_feature_artifacts()


@app.on_event("startup")
def startup() -> None:
    """
    FastAPI lifecycle hook — runs once when the server process starts.

    Loads all ML artifacts into memory before accepting traffic.
    If loading fails, the server will not start (fail-fast).
    """
    _load_runtime_assets()


# ---------------------------------------------------------------------------
# Text preparation — must mirror training preprocessing exactly
# ---------------------------------------------------------------------------
def _prepare_single_text(raw_text: str) -> dict:
    """
    Convert a single raw text string into a one-row DataFrame-compatible dict.

    API users typically paste free-form text (not pre-split 10-K sections).
    We treat the entire input as the Risk Factors section and leave other
    sections empty — custom features (section word counts) will reflect that.

    Returns a dict with keys matching the columns expected by transform_features():
        text, section_risk_factors, section_business, section_mda,
        section_financials

    Interview Q: "What if user sends full 10-K?" — Current design assumes
    risk-heavy snippet; production would call extract_sections() on structured input.
    """
    cleaned = clean_text(raw_text)
    sections = {
        "risk_factors": cleaned,
        "business": "",
        "mda": "",
        "financial_statements": "",
    }
    document_text = build_document_text(sections) or cleaned
    return {
        "text": document_text,
        "section_risk_factors": sections["risk_factors"],
        "section_business": "",
        "section_mda": "",
        "section_financials": "",
    }


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
def health() -> dict[str, str]:
    """
    Liveness probe — confirms the server process is running.

    Does NOT verify model is loaded (use a separate readiness probe in K8s
    if you need that distinction).
    """
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """
    Classify 10-K text into low / medium / high financial risk.

    Inference pipeline (same steps as offline evaluation on one sample):
      1. _prepare_single_text() — NLTK clean + section dict
      2. transform_features()   — TF-IDF + 6 custom numeric features
      3. predict_proba()        — probability vector over 3 classes
      4. argmax                 — pick highest-probability class

    Args:
        request: PredictRequest with validated text field.

    Returns:
        PredictResponse with string label and rounded confidence.

    Raises:
        HTTPException 503: Model artifacts not loaded (startup failure).

    Example:
        POST /predict
        {"text": "The company faces litigation and going concern uncertainty."}
        → {"label": "high", "confidence": 0.85}
    """
    if _model is None or _label_map is None or _feature_artifacts is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    import pandas as pd

    # Build a one-row DataFrame so we can reuse transform_features() from training
    frame = pd.DataFrame([_prepare_single_text(request.text)])
    features = transform_features(frame, _feature_artifacts)

    estimator = _model.estimator
    # CatBoost/AdaBoost need dense arrays; XGBoost accepts sparse CSR matrices
    matrix = features.toarray() if _model.name in {"adaboost", "catboost"} else features
    probabilities = estimator.predict_proba(matrix)[0]

    # Map integer class index back to human-readable label via saved label_map
    predicted_index = int(probabilities.argmax())
    label = _label_map[predicted_index]
    confidence = float(probabilities[predicted_index])
    return PredictResponse(label=label, confidence=round(confidence, 4))
