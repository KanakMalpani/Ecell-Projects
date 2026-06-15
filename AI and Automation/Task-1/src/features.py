"""
Stage 2: convert cleaned text into TF-IDF and custom numeric features.

Machine-learning models need NUMBERS, not English sentences.
This module turns each document into a vector of 5006 numbers:

  - 5000 TF-IDF features  (how important is each word/phrase?)
  - 6 custom features     (word counts, section lengths, ratios)

The fitted vectorizer is saved so the API can transform new text the
same way at prediction time.
"""

from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack, spmatrix
from sklearn.feature_extraction.text import TfidfVectorizer

from .utils import MODELS_DIR, setup_logging

logger = setup_logging(__name__)

# TF-IDF settings — see sklearn docs for full parameter list
TFIDF_MAX_FEATURES = 5000   # keep only the 5000 most informative terms
TFIDF_NGRAM_RANGE = (1, 2)  # capture single words AND two-word phrases


@dataclass
class FeatureArtifacts:
    """
    Container for everything needed to transform NEW text later.

    Saved to models/tfidf_vectorizer.joblib and loaded by the API.
    """
    vectorizer: TfidfVectorizer  # the fitted TF-IDF transformer
    feature_names: list[str]       # human-readable names for each column


def build_custom_features(frame: pd.DataFrame) -> np.ndarray:
    """
    Create 6 hand-crafted numeric features per document.

    These give the model extra signals beyond word importance:
      1. doc_word_count          — total words in the combined text
      2. risk_section_words      — words in the Risk Factors section
      3. business_section_words  — words in the Business section
      4. mda_section_words       — words in the MD&A section
      5. financial_section_words — words in the Financial Statements
      6. risk_section_ratio      — risk words ÷ total words (higher = riskier)
    """
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
            (risk_len / (word_counts + 1)).to_numpy(),  # +1 avoids divide-by-zero
        ]
    )
    return custom.astype(float)


def fit_features(frame: pd.DataFrame) -> tuple[spmatrix, FeatureArtifacts]:
    """
    Learn TF-IDF vocabulary from the training documents and build the
    full feature matrix.

    TF-IDF explained simply:
      TF  = how often a word appears in THIS document
      IDF = how rare the word is across ALL documents
      TF-IDF = TF × IDF  →  rare important words score high

    Returns:
      combined  — sparse matrix of shape (n_documents, 5006)
      artifacts — fitted vectorizer + feature names (saved for the API)
    """
    logger.info("Fitting TF-IDF vectorizer on %s documents", len(frame))
    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        min_df=2,        # ignore words that appear in fewer than 2 docs
        max_df=0.95,     # ignore words in >95% of docs (too common to help)
        sublinear_tf=True,  # use log(1 + tf) to dampen very frequent words
    )
    # frame["text"] is already NLTK-preprocessed in preprocess.py clean_text()
    tfidf_matrix = vectorizer.fit_transform(frame["text"])
    custom_matrix = build_custom_features(frame)

    # Horizontally stack TF-IDF (5000 cols) + custom (6 cols) = 5006 cols
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
    """
    Apply a PREVIOUSLY FITTED vectorizer to new documents.

    Used by the API at prediction time — must use the same vectorizer
    that was saved during training, or the numbers won't match.
    """
    tfidf_matrix = artifacts.vectorizer.transform(frame["text"])
    custom_matrix = build_custom_features(frame)
    return csr_matrix(hstack([tfidf_matrix, custom_matrix]))


def save_feature_artifacts(artifacts: FeatureArtifacts, path=None) -> None:
    """Persist the fitted vectorizer so the API can load it later."""
    path = path or MODELS_DIR / "tfidf_vectorizer.joblib"
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, path)
    logger.info("Saved feature artifacts to %s", path)


def load_feature_artifacts(path=None) -> FeatureArtifacts:
    """Load the saved vectorizer (called by api/app.py on startup)."""
    path = path or MODELS_DIR / "tfidf_vectorizer.joblib"
    return joblib.load(path)
