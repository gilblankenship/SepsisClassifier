"""Visualization utilities for sepsis classifier evaluation."""

from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_curve, auc, confusion_matrix
from typing import Any
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


def plot_roc_curves(
    models: dict[str, tuple[np.ndarray, np.ndarray]],
    literature_benchmarks: dict[str, float] | None = None,
    save: bool = True,
) -> plt.Figure:
    """Plot ROC curves for multiple models with optional literature benchmarks.

    Args:
        models: {name: (y_true, y_prob_positive)}
        literature_benchmarks: {name: auroc} for blood-based reference lines
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    for name, (y_true, y_prob) in models.items():
        fpr, tpr, _ = roc_curve(y_true, y_prob)
        roc_auc = auc(fpr, tpr)
        ax.plot(fpr, tpr, linewidth=2, label=f"{name} (AUC={roc_auc:.3f})")

    if literature_benchmarks:
        for name, auroc_val in literature_benchmarks.items():
            ax.axhline(y=auroc_val, linestyle=":", alpha=0.4)
            ax.annotate(
                f"{name}: {auroc_val:.2f}",
                xy=(0.55, auroc_val),
                fontsize=7,
                alpha=0.6,
            )

    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, label="Random")
    ax.set_xlabel("False Positive Rate (1 - Specificity)")
    ax.set_ylabel("True Positive Rate (Sensitivity)")
    ax.set_title("Urine ELISA Classifier ROC — vs Blood-Based Gold Standard")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(True, alpha=0.3)

    if save:
        ensure_output_dir()
        fig.savefig(OUTPUT_DIR / "roc_curves.png", dpi=150, bbox_inches="tight")
    return fig


def plot_confusion_matrices(
    models: dict[str, tuple[np.ndarray, np.ndarray]],
    save: bool = True,
) -> plt.Figure:
    """Plot confusion matrices for multiple models side by side.

    Args:
        models: {name: (y_true, y_pred)}
    """
    n = len(models)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 3.5))
    if n == 1:
        axes = [axes]

    labels = ["Not Septic", "Septic"]
    for ax, (name, (y_true, y_pred)) in zip(axes, models.items()):
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        sns.heatmap(
            cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=labels, yticklabels=labels, ax=ax,
        )
        ax.set_title(name, fontsize=10)
        ax.set_ylabel("Gold Standard (Blood)")
        ax.set_xlabel("Urine ELISA Prediction")

    fig.suptitle("Confusion Matrices — Urine vs Blood Gold Standard", fontsize=12)
    fig.tight_layout()

    if save:
        ensure_output_dir()
        fig.savefig(OUTPUT_DIR / "confusion_matrices.png", dpi=150, bbox_inches="tight")
    return fig


def plot_decision_boundary(
    classifier: Any,
    X: np.ndarray,
    y: np.ndarray,
    title: str = "Decision Boundary",
    save: bool = True,
    filename: str = "decision_boundary.png",
) -> plt.Figure:
    """Plot 2D decision boundary for CRP/Cr vs IP-10/Cr feature space."""
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create mesh
    x_min, x_max = X[:, 0].min() - 50, X[:, 0].max() + 50
    y_min, y_max = X[:, 1].min() - 20, X[:, 1].max() + 20
    xx, yy = np.meshgrid(
        np.linspace(x_min, x_max, 300),
        np.linspace(y_min, y_max, 300),
    )
    grid = np.c_[xx.ravel(), yy.ravel()]

    if hasattr(classifier, "predict_proba"):
        Z = classifier.predict_proba(grid)[:, 1]
    else:
        Z = classifier.predict(grid).astype(float)
    Z = Z.reshape(xx.shape)

    ax.contourf(xx, yy, Z, levels=20, cmap="RdYlBu_r", alpha=0.6)
    ax.contour(xx, yy, Z, levels=[0.5], colors="k", linewidths=2)

    # Plot samples
    scatter = ax.scatter(
        X[:, 0], X[:, 1], c=y, cmap="RdYlBu_r",
        edgecolors="k", s=60, zorder=5,
    )

    # SepsisDx threshold lines
    ax.axvline(x=300, color="gray", linestyle="--", alpha=0.5, label="CRP/Cr=300 threshold")
    ax.axhline(y=100, color="gray", linestyle="--", alpha=0.5, label="IP-10/Cr=100 threshold")

    ax.set_xlabel("CRP / Creatinine (pg/mg)")
    ax.set_ylabel("IP-10 / Creatinine (pg/mg)")
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=8)

    if save:
        ensure_output_dir()
        fig.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    return fig


def plot_feature_importance(
    feature_names: list[str],
    importances: np.ndarray,
    title: str = "Feature Importance",
    save: bool = True,
) -> plt.Figure:
    """Bar chart of feature importances."""
    fig, ax = plt.subplots(figsize=(8, max(3, len(feature_names) * 0.4)))
    idx = np.argsort(importances)
    ax.barh(range(len(idx)), importances[idx], color="steelblue")
    ax.set_yticks(range(len(idx)))
    ax.set_yticklabels([feature_names[i] for i in idx])
    ax.set_xlabel("Importance")
    ax.set_title(title)

    if save:
        ensure_output_dir()
        fig.savefig(OUTPUT_DIR / "feature_importance.png", dpi=150, bbox_inches="tight")
    return fig
