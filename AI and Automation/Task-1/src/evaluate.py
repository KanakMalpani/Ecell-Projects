"""
Stage 4: evaluate models and produce comparison reports.

WHAT THIS FILE DOES
-------------------
Splits the feature matrix into train/test sets, trains all three boosting
models, scores each on held-out data, generates visual reports, and persists
the winning model for deployment.

WHY IT EXISTS
-------------
Model comparison is not optional — we need objective metrics to justify
choosing XGBoost over AdaBoost/CatBoost. This module is the "experiment
tracker" that produces numbers for reports, slides, and interview answers.

HOW IT FITS IN THE PIPELINE
---------------------------
  Called by run_pipeline.py AFTER features.py produces the sparse matrix.
  Internally calls train.py to fit models, then:
    → reports/evaluation_report.json
    → reports/metrics_comparison.csv
    → reports/{model}_confusion_matrix.png
    → models/best_model.joblib + models/label_map.joblib

KEY CONCEPTS FOR INTERVIEW
--------------------------
  1. Stratified split: preserves class balance in train and test (critical
     for imbalanced or small datasets).
  2. Macro F1 as selection criterion: averages F1 across classes equally —
     better than accuracy when classes are hard to distinguish (e.g. medium).
  3. Confusion matrix: rows = actual, cols = predicted; off-diagonal = errors.
  4. predict_proba vs predict: API uses probabilities for confidence scores.
  5. Sparse/dense handling repeated here and in api/app.py — AdaBoost/CatBoost
     cannot consume scipy.sparse matrices directly.
"""

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


# ---------------------------------------------------------------------------
# Data splitting — reproducible 80/20 hold-out with stratification
# ---------------------------------------------------------------------------
def split_data(features: spmatrix, labels: list[str], test_size: float = 0.2):
    """
    Split features and labels into train (80%) and test (20%) sets.

    Uses stratify=labels when every class has ≥2 samples so that low/medium/high
    proportions are preserved in both splits. Without stratification, a small
    dataset might put all "high" filings in train only — inflating test scores.

    Args:
        features: Sparse matrix (n_samples × n_features) from features.py.
        labels: Parallel list of "low" / "medium" / "high" strings.
        test_size: Fraction held out for evaluation (default 0.2).

    Returns:
        Tuple of (x_train, x_test, y_train, y_test).

    Interview Q: "Why not cross-validation?" — With ~280 samples, a single
    stratified hold-out is simpler; k-fold would be a good extension.
    """
    indices = np.arange(features.shape[0])
    split_kwargs = {
        "test_size": test_size,
        "random_state": RANDOM_STATE,
    }
    class_counts = pd.Series(labels).value_counts()
    # sklearn requires ≥2 samples per class for stratified splitting
    if class_counts.min() >= 2:
        split_kwargs["stratify"] = labels

    train_idx, test_idx = train_test_split(indices, **split_kwargs)
    x_train = features[train_idx]
    x_test = features[test_idx]
    y_train = [labels[i] for i in train_idx]
    y_test = [labels[i] for i in test_idx]
    return x_train, x_test, y_train, y_test


# ---------------------------------------------------------------------------
# Prediction helpers — unify sparse/dense and proba/hard-label paths
# ---------------------------------------------------------------------------
def _predict_proba(model: TrainedModel, features: spmatrix) -> np.ndarray:
    """
    Return per-class probability matrix of shape (n_samples, n_classes).

    Each row sums to 1.0. Example: [0.05, 0.90, 0.05] → 90% confident
    in class index 1 (which maps to a label via int_to_label).

    Falls back to one-hot encoding if the estimator lacks predict_proba
    (defensive — our three models all support it).
    """
    estimator = model.estimator
    if model.name in {"adaboost", "catboost"}:
        matrix = features.toarray()
    else:
        matrix = features

    if hasattr(estimator, "predict_proba"):
        return estimator.predict_proba(matrix)

    # Fallback for models without predict_proba: one-hot encode hard predictions
    preds = np.ravel(estimator.predict(matrix))
    classes = sorted(model.label_encoder, key=model.label_encoder.get)
    proba = np.zeros((len(preds), len(classes)))
    for row, pred in enumerate(preds):
        proba[row, int(pred)] = 1.0
    return proba


def _predict_labels(model: TrainedModel, features: spmatrix, int_to_label: dict[int, str]) -> list[str]:
    """
    Run hard classification and map integer predictions back to strings.

    Args:
        model: TrainedModel wrapper with fitted estimator.
        features: Test-set feature matrix.
        int_to_label: Reverse mapping {0: "high", 1: "low", ...}.

    Returns:
        List of predicted label strings parallel to feature rows.
    """
    estimator = model.estimator
    matrix = features.toarray() if model.name in {"adaboost", "catboost"} else features
    preds = np.ravel(estimator.predict(matrix))
    return [int_to_label[int(pred)] for pred in preds]


# ---------------------------------------------------------------------------
# Per-model metric computation
# ---------------------------------------------------------------------------
def evaluate_model(
    model: TrainedModel,
    features: spmatrix,
    y_true: list[str],
    int_to_label: dict[int, str],
) -> dict:
    """
    Compute all evaluation metrics for one model on the test set.

    Metrics explained (common interview questions):
      accuracy       — overall correct predictions / total
      precision_macro — avg precision per class (TP / (TP+FP)), unweighted
      recall_macro    — avg recall per class (TP / (TP+FN)), unweighted
      f1_macro        — harmonic mean of precision and recall, per-class avg
      mean_confidence — average of max(predict_proba) across test samples

    Macro averaging treats low/medium/high equally — important when "medium"
    is harder and has lower per-class F1 than "high".

    Returns:
        Dict with scalar metrics, classification_report string, confusion
        matrix as nested list, and mean_confidence float.
    """
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


# ---------------------------------------------------------------------------
# Visualization — confusion matrix heatmaps for report slides
# ---------------------------------------------------------------------------
def plot_confusion_matrix(
    matrix: list[list[int]],
    labels: list[str],
    title: str,
    output_path: Path,
) -> None:
    """
    Draw and save a confusion matrix heatmap as PNG.

    Interpretation for interviews:
      - Diagonal cells = correct predictions for that class
      - Row i, col j (i≠j) = actual class i misclassified as j
      - Medium row often has spread across columns (ambiguous language)

    Args:
        matrix: 2D list of counts (from sklearn confusion_matrix).
        labels: Class names in column/row order.
        title: Plot title (e.g. "Xgboost Confusion Matrix").
        output_path: Where to save the PNG (reports/ folder).
    """
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


# ---------------------------------------------------------------------------
# Main evaluation orchestrator — called by run_pipeline.py
# ---------------------------------------------------------------------------
def run_evaluation(
    features: spmatrix,
    labels: list[str],
) -> tuple[dict, str, dict[int, str]]:
    """
    Full evaluation pipeline: split → train → score → report → save best model.

    Workflow:
      1. 80/20 stratified split via split_data()
      2. train_models() on training portion only
      3. evaluate_model() for each of xgboost, adaboost, catboost
      4. Save JSON report, CSV comparison table, confusion matrix PNGs
      5. Select winner by highest f1_macro; dump to best_model.joblib

    Args:
        features: Full-dataset sparse matrix from fit_features().
        labels: Parallel list of risk_label strings.

    Returns:
        report       — nested dict saved to evaluation_report.json
        best_model   — winning model name string (e.g. "xgboost")
        int_to_label — integer → string label map for API inference

    Interview Q: "Why macro F1 over accuracy?" — Accuracy can hide poor
    performance on minority/hard classes; macro F1 forces balanced scrutiny.
    """
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

    # Winner = highest macro F1 (balances performance across all 3 classes)
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

    # Tidy CSV for Excel / presentation tables
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

    # Persist winner for api/app.py to load at startup
    joblib.dump(trained[best_model], MODELS_DIR / "best_model.joblib")
    joblib.dump(int_to_label, MODELS_DIR / "label_map.joblib")

    return report, best_model, int_to_label
