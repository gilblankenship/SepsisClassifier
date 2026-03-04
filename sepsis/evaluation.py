"""Evaluation metrics and gold-standard comparison for sepsis classifiers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold
from typing import Any


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None = None) -> dict:
    """Compute comprehensive classification metrics against gold standard.

    Gold standard = blood-based diagnosis (blood culture + Sepsis-3 / SOFA >= 2).
    """
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "sensitivity": recall_score(y_true, y_pred, zero_division=0),
        "specificity": recall_score(y_true, y_pred, pos_label=0, zero_division=0),
        "precision_ppv": precision_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }

    # Negative predictive value
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    metrics["npv"] = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    metrics["tn"] = int(tn)
    metrics["fp"] = int(fp)
    metrics["fn"] = int(fn)
    metrics["tp"] = int(tp)

    if y_prob is not None and len(np.unique(y_true)) > 1:
        metrics["auroc"] = roc_auc_score(y_true, y_prob)
    else:
        metrics["auroc"] = None

    return metrics


def cross_validate(
    classifier: Any,
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
    seed: int = 42,
) -> pd.DataFrame:
    """Stratified K-Fold cross-validation returning per-fold metrics."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    results = []

    for fold, (train_idx, test_idx) in enumerate(skf.split(X, y), 1):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        clf = _clone_classifier(classifier)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") else None

        fold_metrics = compute_metrics(y_test, y_pred, y_prob)
        fold_metrics["fold"] = fold
        results.append(fold_metrics)

    return pd.DataFrame(results)


def compare_models(
    classifiers: dict[str, Any],
    X: np.ndarray,
    y: np.ndarray,
    n_splits: int = 5,
) -> pd.DataFrame:
    """Compare multiple classifiers via cross-validation.

    Returns a summary table with mean ± std for each metric.
    """
    summaries = []
    for name, clf in classifiers.items():
        cv_results = cross_validate(clf, X, y, n_splits=n_splits)
        summary = {"model": name}
        for col in ["accuracy", "sensitivity", "specificity", "precision_ppv", "f1_score", "auroc"]:
            vals = cv_results[col].dropna()
            if len(vals) > 0:
                summary[f"{col}_mean"] = vals.mean()
                summary[f"{col}_std"] = vals.std()
            else:
                summary[f"{col}_mean"] = None
                summary[f"{col}_std"] = None
        summaries.append(summary)
    return pd.DataFrame(summaries)


def literature_benchmarks() -> dict[str, float]:
    """Blood-based gold standard AUROC benchmarks from literature.

    These represent the performance of blood-based biomarkers for sepsis
    diagnosis, against which we compare our urine ELISA classifier.
    """
    return {
        "Procalcitonin (blood)": 0.84,
        "Presepsin (blood)": 0.87,
        "CRP (blood)": 0.76,
        "CD64 (blood, flow cytometry)": 0.94,
        "IL-6 (blood)": 0.71,
        "PSP (blood)": 0.75,
    }


def _clone_classifier(clf: Any) -> Any:
    """Create a fresh instance of a classifier with the same parameters."""
    params = clf.get_params()
    return clf.__class__(**params)
