"""Stage 4: evaluate models and produce comparison reports."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.sparse import spmatrix
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

from .train import TrainedModel, train_models
from .utils import MODELS_DIR, RANDOM_STATE, REPORTS_DIR, save_json, setup_logging

logger = setup_logging(__name__)


def split_data(features: spmatrix, labels: list[str], test_size: float = 0.2):
    indices = np.arange(features.shape[0])
    split_kwargs = {
        "test_size": test_size,
        "random_state": RANDOM_STATE,
    }
    class_counts = pd.Series(labels).value_counts()
    if class_counts.min() >= 2:
        split_kwargs["stratify"] = labels

    train_idx, test_idx = train_test_split(indices, **split_kwargs)
    x_train = features[train_idx]
    x_test = features[test_idx]
    y_train = [labels[i] for i in train_idx]
    y_test = [labels[i] for i in test_idx]
    return x_train, x_test, y_train, y_test


def _predict_proba(model: TrainedModel, features: spmatrix) -> np.ndarray:
    estimator = model.estimator
    if model.name in {"adaboost", "catboost"}:
        matrix = features.toarray()
    else:
        matrix = features

    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(matrix)

    preds = np.ravel(estimator.predict(matrix))
    classes = sorted(model.label_encoder, key=model.label_encoder.get)
    proba = np.zeros((len(preds), len(classes)))
    for row, pred in enumerate(preds):
        proba[row, int(pred)] = 1.0
    return proba


def _predict_labels(model: TrainedModel, features: spmatrix, int_to_label: dict[int, str]) -> list[str]:
    estimator = model.estimator
    matrix = features.toarray() if model.name in {"adaboost", "catboost"} else features
    preds = np.ravel(estimator.predict(matrix))
    return [int_to_label[int(pred)] for pred in preds]


def evaluate_model(
    model: TrainedModel,
    features: spmatrix,
    y_true: list[str],
    int_to_label: dict[int, str],
) -> dict:
    y_pred = _predict_labels(model, features, int_to_label)
    proba = _predict_proba(model, features)
    confidences = proba.max(axis=1)

    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "classification_report": classification_report(y_true, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=sorted(set(y_true))).tolist(),
        "mean_confidence": float(np.mean(confidences)),
    }
    return metrics


def plot_confusion_matrix(
    matrix: list[list[int]],
    labels: list[str],
    title: str,
    output_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(matrix, cmap="Blues")
    ax.set_xticks(range(len(labels)), labels)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(title)
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, matrix[i][j], ha="center", va="center", color="black")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def run_evaluation(
    features: spmatrix,
    labels: list[str],
) -> tuple[dict, str, dict[int, str]]:
    x_train, x_test, y_train, y_test = split_data(features, labels)
    trained, int_to_label = train_models(x_train, y_train)

    comparison: dict[str, dict] = {}
    for name, model in trained.items():
        logger.info("Evaluating %s", name)
        metrics = evaluate_model(model, x_test, y_test, int_to_label)
        comparison[name] = metrics

        label_order = sorted(set(y_test))
        plot_confusion_matrix(
            metrics["confusion_matrix"],
            label_order,
            title=f"{name.title()} Confusion Matrix",
            output_path=REPORTS_DIR / f"{name}_confusion_matrix.png",
        )

    best_model = max(comparison, key=lambda key: comparison[key]["f1_macro"])
    logger.info("Best model by macro F1: %s", best_model)

    report = {
        "best_model": best_model,
        "models": {
            name: {
                "accuracy": values["accuracy"],
                "precision_macro": values["precision_macro"],
                "recall_macro": values["recall_macro"],
                "f1_macro": values["f1_macro"],
                "mean_confidence": values["mean_confidence"],
                "confusion_matrix": values["confusion_matrix"],
                "classification_report": values["classification_report"],
            }
            for name, values in comparison.items()
        },
    }
    save_json(REPORTS_DIR / "evaluation_report.json", report)

    metrics_table = pd.DataFrame(
        [
            {
                "model": name,
                "accuracy": values["accuracy"],
                "precision": values["precision_macro"],
                "recall": values["recall_macro"],
                "f1": values["f1_macro"],
            }
            for name, values in comparison.items()
        ]
    )
    metrics_table.to_csv(REPORTS_DIR / "metrics_comparison.csv", index=False)

    joblib.dump(trained[best_model], MODELS_DIR / "best_model.joblib")
    joblib.dump(int_to_label, MODELS_DIR / "label_map.joblib")

    return report, best_model, int_to_label
