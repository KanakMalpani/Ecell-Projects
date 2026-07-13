"""
Stage 3: train and compare XGBoost, AdaBoost, and CatBoost classifiers.

WHAT THIS FILE DOES
-------------------
Defines three gradient-boosting ensemble classifiers, trains them on the
TF-IDF feature matrix, and wraps each in a TrainedModel dataclass for
serialization.

WHY IT EXISTS
-------------
Single-model pipelines are hard to defend in interviews. Training three
well-known boosting algorithms on identical features lets evaluate.py pick
the best empirically (macro F1) rather than assuming one algorithm wins.

HOW IT FITS IN THE PIPELINE
---------------------------
  Called by evaluate.py (not run_pipeline.py directly) during run_evaluation().
  Input:  sparse feature matrix + string labels from features.py / preprocess.py
  Output: dict of TrainedModel objects; winner saved as best_model.joblib

Model lineup:
  XGBoost  — handles sparse matrices natively; typically best on text
  AdaBoost — sklearn ensemble over shallow decision trees
  CatBoost — Yandex gradient boosting; needs dense input

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Gradient boosting: sequentially adds weak learners (trees), each
     correcting previous errors — powerful for tabular/sparse text features.
  2. Label encoding: models need integers; mapping is deterministic via
     RISK_LABELS order in utils.py.
  3. Sparse vs dense: XGBoost.fit(sparse) works; AdaBoost/CatBoost need
     .toarray() — memory trade-off on high-dimensional text.
  4. Multi-class objective: objective="multi:softprob" gives probability
     outputs used by API confidence scores.
  5. Hyperparameters: n_estimators, max_depth, learning_rate — standard
     interview topic; values here are reasonable defaults, not grid-searched.
  6. TrainedModel wrapper: bundles estimator + metadata for clean joblib save.
"""

from __future__ import annotations

from dataclasses import dataclass

import joblib
import numpy as np
from catboost import CatBoostClassifier
from scipy.sparse import spmatrix
from sklearn.ensemble import AdaBoostClassifier
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from .utils import MODELS_DIR, RISK_LABELS, RANDOM_STATE, setup_logging

logger = setup_logging(__name__)


# ---------------------------------------------------------------------------
# TrainedModel — serializable wrapper for estimator + metadata
# ---------------------------------------------------------------------------
@dataclass
class TrainedModel:
    """
    Bundle a fitted classifier with its name and label encoding.

    Saved as .joblib and loaded by api/app.py. The API needs both the
    estimator (for predict_proba) and name (to decide sparse vs dense).

    Attributes:
        name: "xgboost", "adaboost", or "catboost".
        estimator: Fitted sklearn-compatible classifier object.
        label_encoder: Maps "low"→int, "medium"→int, "high"→int.
    """

    name: str
    estimator: object
    label_encoder: dict[str, int]


# ---------------------------------------------------------------------------
# Label encoding — strings to integers and back
# ---------------------------------------------------------------------------
def _label_maps(labels: list[str]) -> tuple[dict[str, int], dict[int, str]]:
    """
    Build bidirectional mapping between string labels and integer class indices.

    Classes sorted by RISK_LABELS order ("low", "medium", "high") so the
    mapping is stable across runs regardless of which labels appear in data.

    Args:
        labels: List of "low" / "medium" / "high" from training set.

    Returns:
        to_int:   {"low": 0, "medium": 1, "high": 2} (example)
        to_label: reverse map for prediction decoding
    """
    classes = sorted(set(labels), key=lambda value: RISK_LABELS.index(value))
    to_int = {label: index for index, label in enumerate(classes)}
    to_label = {index: label for label, index in to_int.items()}
    return to_int, to_label


# ---------------------------------------------------------------------------
# Model factory — instantiate untrained classifiers with default hyperparams
# ---------------------------------------------------------------------------
def build_models() -> dict[str, object]:
    """
    Create three untrained classifiers with sensible default hyperparameters.

    All are ensemble methods combining many decision trees into one strong
    predictor. Hyperparameters chosen for small text-classification datasets
    (~280 samples, 5006 features) — moderate depth, subsampling for
    regularization.

    Returns:
        Dict mapping model name → unfitted estimator instance.

    Interview talking points per model:
      XGBoost  — industry standard for structured/sparse data; native sparse support
      AdaBoost — reweights misclassified samples each round; shallow base trees
      CatBoost — ordered boosting, robust defaults; slower, needs dense matrix
    """
    return {
        # XGBoost: fast, handles sparse matrices natively — our typical winner
        "xgboost": XGBClassifier(
            n_estimators=200,       # number of boosting rounds (trees)
            max_depth=6,            # max depth of each tree (controls complexity)
            learning_rate=0.1,      # shrink each tree's contribution (eta)
            subsample=0.9,          # row subsampling — reduces overfitting
            colsample_bytree=0.8,   # feature subsampling per tree
            objective="multi:softprob",  # 3-class softmax probabilities
            eval_metric="mlogloss",      # multiclass log loss
            random_state=RANDOM_STATE,
            n_jobs=-1,              # parallel tree construction
        ),
        # AdaBoost: boosts a series of shallow decision trees
        "adaboost": AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE),
            n_estimators=150,
            learning_rate=0.8,
            random_state=RANDOM_STATE,
        ),
        # CatBoost: gradient boosting with ordered target statistics
        "catboost": CatBoostClassifier(
            iterations=200,
            depth=6,
            learning_rate=0.1,
            loss_function="MultiClass",
            verbose=False,          # suppress per-iteration training logs
            random_seed=RANDOM_STATE,
        ),
    }


# ---------------------------------------------------------------------------
# Training loop — fit all three models on identical data
# ---------------------------------------------------------------------------
def train_models(
    features: spmatrix,
    labels: list[str],
) -> tuple[dict[str, TrainedModel], dict[int, str]]:
    """
    Train all three boosting models on the same feature matrix and labels.

    Args:
        features: Sparse CSR matrix (n_docs × 5006) from features.py.
        labels:   Parallel list of "low" / "medium" / "high" strings.

    Returns:
        trained:      Dict name → TrainedModel with fitted estimator.
        int_to_label: Reverse label map for decoding predictions.

    Note on sparse handling:
        XGBoost accepts scipy.sparse directly (memory efficient).
        CatBoost and AdaBoost require dense .toarray() — can be slow/RAM-heavy
        at scale but manageable with ~280 × 5006 matrix.
    """
    label_to_int, int_to_label = _label_maps(labels)
    y = np.array([label_to_int[label] for label in labels])

    trained: dict[str, TrainedModel] = {}
    for name, estimator in build_models().items():
        logger.info("Training %s", name)

        # CatBoost and AdaBoost don't accept sparse matrices — convert to dense
        if name == "catboost":
            estimator.fit(features.toarray(), y)
        elif name == "adaboost":
            estimator.fit(features.toarray(), y)
        else:
            estimator.fit(features, y)  # XGBoost handles sparse directly

        trained[name] = TrainedModel(
            name=name,
            estimator=estimator,
            label_encoder=label_to_int,
        )
        logger.info("Finished training %s", name)

    return trained, int_to_label


# ---------------------------------------------------------------------------
# Optional persistence — save individual models (evaluate.py saves best only)
# ---------------------------------------------------------------------------
def save_models(
    trained: dict[str, TrainedModel],
    int_to_label: dict[int, str],
    output_dir=None,
) -> None:
    """
    Save each trained model and the label map to the models/ folder.

    evaluate.py saves only the best model; this function is available if you
    want all three persisted for offline analysis.

    Args:
        trained: Output of train_models().
        int_to_label: Integer → string label mapping.
        output_dir: Target directory (defaults to MODELS_DIR).
    """
    output_dir = output_dir or MODELS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for model in trained.values():
        path = output_dir / f"{model.name}_model.joblib"
        joblib.dump(model, path)
        logger.info("Saved %s to %s", model.name, path)

    joblib.dump(int_to_label, output_dir / "label_map.joblib")
