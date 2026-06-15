"""
Stage 3: train and compare XGBoost, AdaBoost, and CatBoost classifiers.

Three different "gradient boosting" algorithms learn patterns from the
TF-IDF feature matrix and predict one of three classes:
  0 = low risk,  1 = medium risk,  2 = high risk

After training, each model is saved individually. evaluate.py picks
the best one and copies it to models/best_model.joblib.
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


@dataclass
class TrainedModel:
    """
    Wrapper that bundles a trained estimator with its metadata.

    Saved as a .joblib file so the API can load and use it directly.
    """
    name: str                        # "xgboost", "adaboost", or "catboost"
    estimator: object                # the actual sklearn / xgboost model
    label_encoder: dict[str, int]    # maps "low"→0, "medium"→1, "high"→2


def _label_maps(labels: list[str]) -> tuple[dict[str, int], dict[int, str]]:
    """
    Convert text labels to integers (and back).

    Models need numbers, not strings. We sort by RISK_LABELS order so
    the mapping is always consistent: high=0, low=1, medium=2.
    """
    classes = sorted(set(labels), key=lambda value: RISK_LABELS.index(value))
    to_int = {label: index for index, label in enumerate(classes)}
    to_label = {index: label for label, index in to_int.items()}
    return to_int, to_label


def build_models() -> dict[str, object]:
    """
    Create three untrained classifiers with sensible default hyperparameters.

    All are "ensemble" methods — they combine many weak decision trees
    to make a strong final prediction.
    """
    return {
        # XGBoost: fast, handles sparse matrices natively — our winner
        "xgboost": XGBClassifier(
            n_estimators=200,       # number of boosting rounds (trees)
            max_depth=6,            # max depth of each tree
            learning_rate=0.1,        # shrink each tree's contribution
            subsample=0.9,          # use 90% of rows per tree (reduces overfitting)
            colsample_bytree=0.8,   # use 80% of features per tree
            objective="multi:softprob",  # 3-class classification with probabilities
            eval_metric="mlogloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,              # use all CPU cores
        ),
        # AdaBoost: boosts a series of shallow decision trees
        "adaboost": AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE),
            n_estimators=150,
            learning_rate=0.8,
            random_state=RANDOM_STATE,
        ),
        # CatBoost: gradient boosting with built-in categorical support
        "catboost": CatBoostClassifier(
            iterations=200,
            depth=6,
            learning_rate=0.1,
            loss_function="MultiClass",
            verbose=False,          # suppress training log spam
            random_seed=RANDOM_STATE,
        ),
    }


def train_models(
    features: spmatrix,
    labels: list[str],
) -> tuple[dict[str, TrainedModel], dict[int, str]]:
    """
    Train all three models on the same feature matrix and label list.

    Args:
        features — sparse matrix from features.py (n_docs × 5006)
        labels   — list of "low" / "medium" / "high" strings

    Returns:
        trained     — dict mapping model name → TrainedModel wrapper
        int_to_label — reverse map {0: "high", 1: "low", 2: "medium"}
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


def save_models(
    trained: dict[str, TrainedModel],
    int_to_label: dict[int, str],
    output_dir=None,
) -> None:
    """Save each trained model and the label map to models/ folder."""
    output_dir = output_dir or MODELS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for model in trained.values():
        path = output_dir / f"{model.name}_model.joblib"
        joblib.dump(model, path)
        logger.info("Saved %s to %s", model.name, path)

    joblib.dump(int_to_label, output_dir / "label_map.joblib")
