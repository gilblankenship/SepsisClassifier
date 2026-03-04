"""Hyperparameter tuning, threshold optimization, and calibration for sepsis classifiers."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    roc_curve,
    precision_recall_curve,
    f1_score,
    make_scorer,
    recall_score,
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from typing import Any


# ──────────────────────────────────────────────────────────────────────
# Hyperparameter Tuning
# ──────────────────────────────────────────────────────────────────────

PARAM_GRIDS = {
    "LogisticRegression": {
        "C": [0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
        "class_weight": ["balanced", None],
    },
    "RandomForest": {
        "n_estimators": [100, 200, 500],
        "max_depth": [3, 5, 8, None],
        "min_samples_leaf": [1, 3, 5],
        "class_weight": ["balanced", "balanced_subsample"],
    },
    "XGBoost": {
        "n_estimators": [100, 200, 500],
        "max_depth": [3, 4, 6],
        "learning_rate": [0.01, 0.05, 0.1, 0.2],
        "subsample": [0.8, 1.0],
    },
}


def tune_logistic(X: np.ndarray, y: np.ndarray, cv: int = 5) -> dict:
    """Grid search for logistic regression."""
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(solver="lbfgs", max_iter=1000, random_state=42)
    scorer = make_scorer(recall_score, pos_label=1)

    grid = GridSearchCV(
        model,
        PARAM_GRIDS["LogisticRegression"],
        cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42),
        scoring={"auroc": "roc_auc", "sensitivity": scorer, "f1": "f1"},
        refit="auroc",
        n_jobs=-1,
    )
    grid.fit(X_scaled, y)

    return {
        "best_params": grid.best_params_,
        "best_auroc": grid.best_score_,
        "cv_results": pd.DataFrame(grid.cv_results_),
        "best_estimator": grid.best_estimator_,
        "scaler": scaler,
    }


def tune_random_forest(X: np.ndarray, y: np.ndarray, cv: int = 5) -> dict:
    """Grid search for random forest."""
    model = RandomForestClassifier(random_state=42, n_jobs=-1)
    scorer = make_scorer(recall_score, pos_label=1)

    grid = GridSearchCV(
        model,
        PARAM_GRIDS["RandomForest"],
        cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42),
        scoring={"auroc": "roc_auc", "sensitivity": scorer, "f1": "f1"},
        refit="auroc",
        n_jobs=-1,
    )
    grid.fit(X, y)

    return {
        "best_params": grid.best_params_,
        "best_auroc": grid.best_score_,
        "cv_results": pd.DataFrame(grid.cv_results_),
        "best_estimator": grid.best_estimator_,
    }


def tune_xgboost(X: np.ndarray, y: np.ndarray, cv: int = 5) -> dict:
    """Grid search for XGBoost."""
    import xgboost as xgb

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_neg = np.sum(y == 0)
    n_pos = np.sum(y == 1)
    spw = n_neg / max(n_pos, 1)

    model = xgb.XGBClassifier(
        scale_pos_weight=spw,
        eval_metric="logloss",
        random_state=42,
        verbosity=0,
    )
    scorer = make_scorer(recall_score, pos_label=1)

    grid = GridSearchCV(
        model,
        PARAM_GRIDS["XGBoost"],
        cv=StratifiedKFold(n_splits=cv, shuffle=True, random_state=42),
        scoring={"auroc": "roc_auc", "sensitivity": scorer, "f1": "f1"},
        refit="auroc",
        n_jobs=-1,
    )
    grid.fit(X_scaled, y)

    return {
        "best_params": grid.best_params_,
        "best_auroc": grid.best_score_,
        "cv_results": pd.DataFrame(grid.cv_results_),
        "best_estimator": grid.best_estimator_,
        "scaler": scaler,
    }


# ──────────────────────────────────────────────────────────────────────
# Threshold Optimization
# ──────────────────────────────────────────────────────────────────────

def optimize_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    strategy: str = "max_sensitivity_90spec",
) -> dict:
    """Find optimal classification threshold for clinical use.

    Strategies:
        - "max_f1": maximize F1 score
        - "max_sensitivity_90spec": maximize sensitivity while keeping specificity >= 0.90
        - "max_youden": maximize Youden's J (sensitivity + specificity - 1)
        - "min_missed": minimize false negatives (maximize sensitivity with specificity >= 0.80)
    """
    fpr, tpr, thresholds_roc = roc_curve(y_true, y_prob)
    specificity = 1 - fpr

    if strategy == "max_f1":
        precision, recall, thresholds_pr = precision_recall_curve(y_true, y_prob)
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_idx = np.argmax(f1_scores[:-1])
        best_threshold = thresholds_pr[best_idx]
        best_metric = f1_scores[best_idx]

    elif strategy == "max_sensitivity_90spec":
        valid = specificity >= 0.90
        if valid.any():
            valid_tpr = tpr[valid]
            valid_thresh = thresholds_roc[valid[:-1]] if len(thresholds_roc) < len(valid) else thresholds_roc[valid]
            best_idx = np.argmax(valid_tpr[:len(valid_thresh)])
            best_threshold = valid_thresh[best_idx]
            best_metric = valid_tpr[best_idx]
        else:
            best_threshold = 0.5
            best_metric = tpr[np.argmin(np.abs(thresholds_roc - 0.5))]

    elif strategy == "max_youden":
        youden_j = tpr + specificity - 1
        best_idx = np.argmax(youden_j[:-1])
        best_threshold = thresholds_roc[best_idx]
        best_metric = youden_j[best_idx]

    elif strategy == "min_missed":
        valid = specificity >= 0.80
        if valid.any():
            valid_tpr = tpr[valid]
            valid_thresh = thresholds_roc[valid[:-1]] if len(thresholds_roc) < len(valid) else thresholds_roc[valid]
            best_idx = np.argmax(valid_tpr[:len(valid_thresh)])
            best_threshold = valid_thresh[best_idx]
            best_metric = valid_tpr[best_idx]
        else:
            best_threshold = 0.3
            best_metric = None

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Compute metrics at optimal threshold
    y_pred_opt = (y_prob >= best_threshold).astype(int)
    from sepsis.evaluation import compute_metrics
    metrics = compute_metrics(y_true, y_pred_opt, y_prob)
    metrics["optimal_threshold"] = float(best_threshold)
    metrics["strategy"] = strategy
    metrics["strategy_metric"] = float(best_metric) if best_metric is not None else None

    return metrics


def optimize_all_strategies(y_true: np.ndarray, y_prob: np.ndarray) -> pd.DataFrame:
    """Run all threshold optimization strategies and compare results."""
    strategies = ["max_f1", "max_sensitivity_90spec", "max_youden", "min_missed"]
    results = []
    for strat in strategies:
        metrics = optimize_threshold(y_true, y_prob, strategy=strat)
        results.append(metrics)
    return pd.DataFrame(results)


# ──────────────────────────────────────────────────────────────────────
# Calibration
# ──────────────────────────────────────────────────────────────────────

def compute_calibration(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
) -> dict:
    """Compute calibration curve data for reliability diagrams."""
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")

    # Expected Calibration Error (ECE)
    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i + 1])
        if mask.sum() > 0:
            bin_acc = y_true[mask].mean()
            bin_conf = y_prob[mask].mean()
            ece += mask.sum() / len(y_true) * abs(bin_acc - bin_conf)

    return {
        "prob_true": prob_true,
        "prob_pred": prob_pred,
        "ece": ece,
        "n_bins": n_bins,
    }
