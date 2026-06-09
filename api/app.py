"""Stage 5: FastAPI deployment for the best trained model."""

from __future__ import annotations

from pathlib import Path
import sys

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features import load_feature_artifacts, transform_features
from src.preprocess import build_document_text, clean_text
from src.train import TrainedModel

MODELS_DIR = PROJECT_ROOT / "models"


class PredictRequest(BaseModel):
    text: str = Field(..., min_length=20, description="Raw 10-K filing text or section text")


class PredictResponse(BaseModel):
    label: str
    confidence: float


app = FastAPI(
    title="10-K Financial Risk Classifier",
    description="Classifies SEC 10-K filing text into low, medium, or high financial risk.",
    version="1.0.0",
)

_model: TrainedModel | None = None
_label_map: dict[int, str] | None = None
_feature_artifacts = None


def _load_runtime_assets() -> None:
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
    _load_runtime_assets()


def _prepare_single_text(raw_text: str) -> dict:
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
    return {"status": "ok"}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest) -> PredictResponse:
    if _model is None or _label_map is None or _feature_artifacts is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    import pandas as pd

    frame = pd.DataFrame([_prepare_single_text(request.text)])
    features = transform_features(frame, _feature_artifacts)

    estimator = _model.estimator
    matrix = features.toarray() if _model.name in {"adaboost", "catboost"} else features
    probabilities = estimator.predict_proba(matrix)[0]
    predicted_index = int(probabilities.argmax())
    label = _label_map[predicted_index]
    confidence = float(probabilities[predicted_index])
    return PredictResponse(label=label, confidence=round(confidence, 4))
