"""Stage 2: convert cleaned text into TF-IDF and custom numeric features."""

from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack, spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer

from .utils import MODELS_DIR, setup_logging

logger = setup_logging(__name__)

TFIDF_MAX_FEATURES = 5000
TFIDF_NGRAM_RANGE = (1, 2)


@dataclass
class FeatureArtifacts:
    vectorizer: TfidfVectorizer
    feature_names: list[str]


def build_custom_features(frame: pd.DataFrame) -> np.ndarray:
    word_counts = frame["text"].str.split().str.len().fillna(0)
    risk_len = frame["section_risk_factors"].str.split().str.len().fillna(0)
    business_len = frame["section_business"].str.split().str.len().fillna(0)
    mda_len = frame["section_mda"].str.split().str.len().fillna(0)
    financial_len = frame["section_financials"].str.split().str.len().fillna(0)

    custom = np.column_stack(
        [
            word_counts.to_numpy(),
            risk_len.to_numpy(),
            business_len.to_numpy(),
            mda_len.to_numpy(),
            financial_len.to_numpy(),
            (risk_len / (word_counts + 1)).to_numpy(),
        ]
    )
    return custom.astype(float)


def fit_features(frame: pd.DataFrame) -> tuple[spmatrix, FeatureArtifacts]:
    logger.info("Fitting TF-IDF vectorizer on %s documents", len(frame))
    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        min_df=2,
        max_df=0.95,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(frame["text"])
    custom_matrix = build_custom_features(frame)
    combined = csr_matrix(hstack([tfidf_matrix, custom_matrix]))

    names = list(vectorizer.get_feature_names_out()) + [
        "doc_word_count",
        "risk_section_words",
        "business_section_words",
        "mda_section_words",
        "financial_section_words",
        "risk_section_ratio",
    ]
    artifacts = FeatureArtifacts(vectorizer=vectorizer, feature_names=names)
    logger.info("Feature matrix shape: %s", combined.shape)
    return combined, artifacts


def transform_features(frame: pd.DataFrame, artifacts: FeatureArtifacts) -> spmatrix:
    tfidf_matrix = artifacts.vectorizer.transform(frame["text"])
    custom_matrix = build_custom_features(frame)
    return csr_matrix(hstack([tfidf_matrix, custom_matrix]))


def save_feature_artifacts(artifacts: FeatureArtifacts, path=None) -> None:
    path = path or MODELS_DIR / "tfidf_vectorizer.joblib"
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, path)
    logger.info("Saved feature artifacts to %s", path)


def load_feature_artifacts(path=None) -> FeatureArtifacts:
    path = path or MODELS_DIR / "tfidf_vectorizer.joblib"
    return joblib.load(path)
