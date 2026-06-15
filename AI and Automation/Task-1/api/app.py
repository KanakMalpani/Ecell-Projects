"""
Stage 5: FastAPI deployment for the best trained model.

After running run_pipeline.py, start this server:

    uvicorn api.app:app --reload

Then visit http://127.0.0.1:8000/docs for interactive Swagger UI.

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

# Make sure Python can import from the project root (src/, etc.)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features import load_feature_artifacts, transform_features
from src.preprocess import build_document_text, clean_text
from src.train import TrainedModel

MODELS_DIR = PROJECT_ROOT / "models"


# ---------------------------------------------------------------------------
# Request / Response schemas (Pydantic validates incoming JSON automatically)
# ---------------------------------------------------------------------------
class PredictRequest(BaseModel):
    """What the client sends to POST /predict."""
    text: str = Field(..., min_length=20, description="Raw 10-K filing text or section text")


class PredictResponse(BaseModel):
    """What the API returns after prediction."""
    label: str        # "low", "medium", or "high"
    confidence: float  # 0.0 to 1.0 — how sure the model is


# ---------------------------------------------------------------------------
# FastAPI app instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="10-K Financial Risk Classifier",
    description="Classifies SEC 10-K filing text into low, medium, or high financial risk.",
    version="1.0.0",
)

# These globals are populated once at startup and reused for every request
_model: TrainedModel | None = None
_label_map: dict[int, str] | None = None
_feature_artifacts = None


def _load_runtime_assets() -> None:
    """
    Load the trained model, label map, and TF-IDF vectorizer from disk.

    Raises FileNotFoundError if run_pipeline.py hasn't been run yet.
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
    """Called once when the server starts — loads model into memory."""
    _load_runtime_assets()


def _prepare_single_text(raw_text: str) -> dict:
    """
    Turn a raw text string into the same DataFrame format used during training.

    For API requests the user typically sends free-form text (not pre-split
    sections), so we treat the entire input as the Risk Factors section.
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


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check — returns ok if the server is running."""
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    """
    Classify a piece of 10-K text into low / medium / high risk.

    Flow:
      1. Clean the input text (same preprocessing as training)
      2. Convert to TF-IDF feature vector
      3. Run model.predict_proba() → probabilities for each class
      4. Return the class with the highest probability + confidence score

    Example:
        POST /predict
        {"text": "The company faces litigation and going concern uncertainty."}

        → {"label": "high", "confidence": 0.85}
    """
    if _model is None or _label_map is None or _feature_artifacts is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    import pandas as pd

    # Build a one-row DataFrame so we can reuse transform_features()
    frame = pd.DataFrame([_prepare_single_text(request.text)])
    features = transform_features(frame, _feature_artifacts)

    estimator = _model.estimator
    # CatBoost/AdaBoost need dense arrays; XGBoost accepts sparse
    matrix = features.toarray() if _model.name in {"adaboost", "catboost"} else features
    probabilities = estimator.predict_proba(matrix)[0]

    # Pick the class with the highest probability
    predicted_index = int(probabilities.argmax())
    label = _label_map[predicted_index]
    confidence = float(probabilities[predicted_index])
    return PredictResponse(label=label, confidence=round(confidence, 4))
