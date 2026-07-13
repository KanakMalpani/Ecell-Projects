"""
Stage 2: convert cleaned text into TF-IDF and custom numeric features.

WHAT THIS FILE DOES
-------------------
Transforms each preprocessed 10-K document from a string of words into a
numeric feature vector suitable for sklearn/XGBoost classifiers.

WHY IT EXISTS
-------------
ML models cannot read English. TF-IDF captures lexical importance (which
words/phrases distinguish documents), while custom features inject domain
structure (section lengths, risk-section ratio) without relying solely on
vocabulary overlap.

HOW IT FITS IN THE PIPELINE
---------------------------
  Input:  DataFrame from preprocess.py (column "text" + section columns)
  Output: scipy.sparse.csr_matrix of shape (n_docs, 5006)
          FeatureArtifacts saved to models/tfidf_vectorizer.joblib
  Used by: run_pipeline.py (fit), evaluate.py (train), api/app.py (transform)

Feature breakdown:
  5000 columns — TF-IDF (unigrams + bigrams, max 5000 terms)
  6 columns    — custom numeric (word counts + risk ratio)

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. TF-IDF = Term Frequency × Inverse Document Frequency
     - High TF-IDF: word is frequent in THIS doc but rare across corpus
     - sublinear_tf=True uses log(1+tf) to dampen very common terms
  2. N-grams (1,2): captures phrases like "going concern", not just "going"
  3. min_df=2, max_df=0.95: vocabulary filtering to reduce noise/overfitting
  4. Sparse matrices: 5006 × 283 docs mostly zeros — memory efficient
  5. fit vs transform: fit learns vocabulary on training corpus; transform
     applies fixed vocabulary at inference (critical for API consistency)
  6. No label leakage: risk_score is NOT a feature — only text-derived signals
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

# ---------------------------------------------------------------------------
# TF-IDF hyperparameters — tuned for SEC filing vocabulary size
# ---------------------------------------------------------------------------
TFIDF_MAX_FEATURES = 5000   # cap vocabulary at 5000 most informative terms
TFIDF_NGRAM_RANGE = (1, 2)  # unigrams ("litigation") + bigrams ("going concern")


# ---------------------------------------------------------------------------
# FeatureArtifacts — serializable bundle for inference-time transformation
# ---------------------------------------------------------------------------
@dataclass
class FeatureArtifacts:
    """
    Container for everything needed to transform NEW text at prediction time.

    Saved to models/tfidf_vectorizer.joblib and loaded by api/app.py on startup.
    Without this artifact, the API cannot reproduce training-time feature values.

    Attributes:
        vectorizer: Fitted sklearn TfidfVectorizer (vocabulary + IDF weights).
        feature_names: Human-readable column names (5000 terms + 6 custom).
    """

    vectorizer: TfidfVectorizer
    feature_names: list[str]


# ---------------------------------------------------------------------------
# Custom (hand-crafted) features — domain knowledge beyond bag-of-words
# ---------------------------------------------------------------------------
def build_custom_features(frame: pd.DataFrame) -> np.ndarray:
    """
    Create 6 hand-crafted numeric features per document.

    These complement TF-IDF by encoding document structure:
      1. doc_word_count          — total words in combined text
      2. risk_section_words      — words in Risk Factors section alone
      3. business_section_words  — words in Business section
      4. mda_section_words       — words in MD&A section
      5. financial_section_words — words in Financial Statements section
      6. risk_section_ratio      — risk_section_words / doc_word_count

    Interview insight: risk_section_ratio proxies "how much of this filing
    is devoted to risk disclosure" — a simple but interpretable signal.

    Args:
        frame: DataFrame with "text" and section_* columns from preprocess.py.

    Returns:
        Dense numpy array of shape (n_docs, 6), dtype float.
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


# ---------------------------------------------------------------------------
# Training-time feature fitting — learns vocabulary from corpus
# ---------------------------------------------------------------------------
def fit_features(frame: pd.DataFrame) -> tuple[spmatrix, FeatureArtifacts]:
    """
    Learn TF-IDF vocabulary from documents and build the full feature matrix.

    TF-IDF intuition for interviews:
      TF  (term frequency)  — how often term t appears in document d
      IDF (inverse doc freq) — log(N / df_t), penalizes terms in many docs
      TF-IDF(t,d) = TF(t,d) × IDF(t)

    Steps:
      1. Fit TfidfVectorizer on frame["text"] (NLTK-preprocessed strings)
      2. Build custom 6-column numeric matrix
      3. Horizontally stack → sparse CSR matrix (5000 + 6 = 5006 columns)

    Args:
        frame: Preprocessed DataFrame with at least a "text" column.

    Returns:
        combined  — sparse matrix (n_docs × 5006)
        artifacts — fitted vectorizer + feature names for persistence
    """
    logger.info("Fitting TF-IDF vectorizer on %s documents", len(frame))
    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        min_df=2,           # drop terms appearing in <2 documents (typos/noise)
        max_df=0.95,        # drop terms in >95% of docs (too common to discriminate)
        sublinear_tf=True,  # apply 1 + log(tf) instead of raw count
    )
    # frame["text"] is already NLTK-preprocessed in preprocess.py clean_text()
    tfidf_matrix = vectorizer.fit_transform(frame["text"])
    custom_matrix = build_custom_features(frame)

    # hstack combines sparse TF-IDF with dense custom features horizontally
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


# ---------------------------------------------------------------------------
# Inference-time transformation — applies PRE-FITTED vectorizer
# ---------------------------------------------------------------------------
def transform_features(frame: pd.DataFrame, artifacts: FeatureArtifacts) -> spmatrix:
    """
    Apply a previously fitted vectorizer to new documents (API inference path).

    CRITICAL: Must use the same artifacts saved during training. Re-fitting
    on a single prediction row would produce a different vocabulary → wrong
    features → garbage predictions.

    Args:
        frame: One or more rows with "text" and section columns.
        artifacts: Loaded FeatureArtifacts from tfidf_vectorizer.joblib.

    Returns:
        Sparse feature matrix ready for model.predict_proba().
    """
    tfidf_matrix = artifacts.vectorizer.transform(frame["text"])
    custom_matrix = build_custom_features(frame)
    return csr_matrix(hstack([tfidf_matrix, custom_matrix]))


# ---------------------------------------------------------------------------
# Artifact persistence — bridge between offline training and online serving
# ---------------------------------------------------------------------------
def save_feature_artifacts(artifacts: FeatureArtifacts, path=None) -> None:
    """
    Persist fitted vectorizer to disk via joblib.

    Args:
        artifacts: FeatureArtifacts from fit_features().
        path: Optional override; defaults to models/tfidf_vectorizer.joblib.
    """
    path = path or MODELS_DIR / "tfidf_vectorizer.joblib"
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, path)
    logger.info("Saved feature artifacts to %s", path)


def load_feature_artifacts(path=None) -> FeatureArtifacts:
    """
    Load saved vectorizer for API inference.

    Called by api/app.py during server startup.

    Args:
        path: Optional override; defaults to models/tfidf_vectorizer.joblib.

    Returns:
        FeatureArtifacts ready for transform_features().
    """
    path = path or MODELS_DIR / "tfidf_vectorizer.joblib"
    return joblib.load(path)
