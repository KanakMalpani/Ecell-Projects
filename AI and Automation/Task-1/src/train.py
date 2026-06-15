"""Stage 3: train and compare XGBoost, AdaBoost, and CatBoost classifiers."""

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
    name: str
    estimator: object
    label_encoder: dict[str, int]


def _label_maps(labels: list[str]) -> tuple[dict[str, int], dict[int, str]]:
    classes = sorted(set(labels), key=lambda value: RISK_LABELS.index(value))
    to_int = {label: index for index, label in enumerate(classes)}
    to_label = {index: label for label, index in to_int.items()}
    return to_int, to_label


def build_models() -> dict[str, object]:
    return {
        "xgboost": XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.9,
            colsample_bytree=0.8,
            objective="multi:softprob",
            eval_metric="mlogloss",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
        "adaboost": AdaBoostClassifier(
            estimator=DecisionTreeClassifier(max_depth=4, random_state=RANDOM_STATE),
            n_estimators=150,
            learning_rate=0.8,
            random_state=RANDOM_STATE,
        ),
        "catboost": CatBoostClassifier(
            iterations=200,
            depth=6,
            learning_rate=0.1,
            loss_function="MultiClass",
            verbose=False,
            random_seed=RANDOM_STATE,
        ),
    }


def train_models(
    features: spmatrix,
    labels: list[str],
) -> tuple[dict[str, TrainedModel], dict[int, str]]:
    label_to_int, int_to_label = _label_maps(labels)
    y = np.array([label_to_int[label] for label in labels])

    trained: dict[str, TrainedModel] = {}
    for name, estimator in build_models().items():
        logger.info("Training %s", name)
        if name == "catboost":
            estimator.fit(features.toarray(), y)
        elif name == "adaboost":
            estimator.fit(features.toarray(), y)
        else:
            estimator.fit(features, y)

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
    output_dir = output_dir or MODELS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    for model in trained.values():
        path = output_dir / f"{model.name}_model.joblib"
        joblib.dump(model, path)
        logger.info("Saved %s to %s", model.name, path)

    joblib.dump(int_to_label, output_dir / "label_map.joblib")
