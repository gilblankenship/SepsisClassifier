"""SHAP-based model explainability for sepsis classifiers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Any

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    return OUTPUT_DIR


def compute_shap_values(
    classifier: Any,
    X: np.ndarray,
    feature_names: list[str],
    background_size: int = 100,
    seed: int = 42,
) -> shap.Explanation:
    """Compute SHAP values for a trained classifier.

    Uses KernelExplainer for model-agnostic explanations, which works
    with all classifier types (baseline, logistic, RF, XGBoost, neural net).
    """
    rng = np.random.default_rng(seed)
    bg_idx = rng.choice(len(X), size=min(background_size, len(X)), replace=False)
    background = X[bg_idx]

    explainer = shap.KernelExplainer(
        lambda x: classifier.predict_proba(x)[:, 1],
        background,
    )
    shap_values = explainer.shap_values(X, silent=True)

    explanation = shap.Explanation(
        values=shap_values,
        base_values=explainer.expected_value,
        data=X,
        feature_names=feature_names,
    )
    return explanation


def compute_shap_tree(
    classifier: Any,
    X: np.ndarray,
    feature_names: list[str],
) -> shap.Explanation:
    """Compute SHAP values using TreeExplainer (fast, for tree-based models)."""
    # Access the underlying sklearn/xgb model
    if hasattr(classifier, "_model"):
        model = classifier._model
        # If the classifier has a scaler, we need to transform X
        if hasattr(classifier, "_scaler"):
            X = classifier._scaler.transform(X)
    else:
        model = classifier

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    # For binary classification, TreeExplainer may return a list or 3D array
    if isinstance(shap_values, list):
        shap_values = shap_values[1]  # Class 1 (Septic)
    elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        shap_values = shap_values[:, :, 1]  # Class 1 (Septic)

    base_val = explainer.expected_value
    if isinstance(base_val, (list, np.ndarray)) and len(base_val) > 1:
        base_val = base_val[1]

    explanation = shap.Explanation(
        values=shap_values,
        base_values=base_val,
        data=X,
        feature_names=feature_names,
    )
    return explanation


def explain_single_patient(
    classifier: Any,
    patient_data: np.ndarray,
    feature_names: list[str],
    background: np.ndarray,
    patient_label: str = "Patient",
) -> dict:
    """Generate a human-readable explanation for a single patient prediction.

    Returns a dict with prediction, probability, and per-feature contributions.
    """
    pred = classifier.predict(patient_data.reshape(1, -1))[0]
    prob = classifier.predict_proba(patient_data.reshape(1, -1))[0, 1]

    explainer = shap.KernelExplainer(
        lambda x: classifier.predict_proba(x)[:, 1],
        background,
    )
    shap_values = explainer.shap_values(patient_data.reshape(1, -1), silent=True)

    contributions = []
    for i, name in enumerate(feature_names):
        contributions.append({
            "feature": name,
            "value": float(patient_data[i]),
            "shap_value": float(shap_values[0][i]),
            "direction": "increases" if shap_values[0][i] > 0 else "decreases",
        })

    # Sort by absolute SHAP value
    contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

    return {
        "patient": patient_label,
        "prediction": "Septic" if pred == 1 else "Not Septic",
        "probability": float(prob),
        "base_rate": float(explainer.expected_value),
        "contributions": contributions,
    }


def plot_shap_summary(
    explanation: shap.Explanation,
    title: str = "SHAP Feature Importance",
    save: bool = True,
) -> plt.Figure:
    """SHAP beeswarm summary plot showing feature impact distribution."""
    fig, ax = plt.subplots(figsize=(10, 5))
    shap.summary_plot(explanation, show=False, plot_size=None)
    plt.title(title)
    plt.tight_layout()

    if save:
        ensure_output_dir()
        fig = plt.gcf()
        fig.savefig(OUTPUT_DIR / "shap_summary.png", dpi=150, bbox_inches="tight")
    return plt.gcf()


def plot_shap_bar(
    explanation: shap.Explanation,
    title: str = "Mean |SHAP| Feature Importance",
    save: bool = True,
) -> plt.Figure:
    """Bar plot of mean absolute SHAP values per feature."""
    fig, ax = plt.subplots(figsize=(8, max(3, len(explanation.feature_names) * 0.5)))
    shap.plots.bar(explanation, show=False, ax=ax)
    ax.set_title(title)

    if save:
        ensure_output_dir()
        fig.savefig(OUTPUT_DIR / "shap_bar.png", dpi=150, bbox_inches="tight")
    return fig


def plot_shap_waterfall(
    explanation: shap.Explanation,
    sample_idx: int = 0,
    title: str | None = None,
    save: bool = True,
    filename: str = "shap_waterfall.png",
) -> plt.Figure:
    """Waterfall plot showing SHAP decomposition for a single prediction."""
    fig = plt.figure(figsize=(10, 4))
    shap.plots.waterfall(explanation[sample_idx], show=False)
    if title:
        plt.title(title)

    if save:
        ensure_output_dir()
        plt.savefig(OUTPUT_DIR / filename, dpi=150, bbox_inches="tight")
    return plt.gcf()


def plot_shap_dependence(
    explanation: shap.Explanation,
    feature: str | int = 0,
    save: bool = True,
) -> plt.Figure:
    """Dependence plot showing feature value vs SHAP impact."""
    fig, ax = plt.subplots(figsize=(8, 5))
    shap.dependence_plot(feature, explanation.values, explanation.data,
                         feature_names=explanation.feature_names, ax=ax, show=False)

    if save:
        ensure_output_dir()
        fname = feature if isinstance(feature, str) else explanation.feature_names[feature]
        safe_name = fname.lower().replace("/", "_").replace(" ", "_")
        fig.savefig(OUTPUT_DIR / f"shap_dependence_{safe_name}.png", dpi=150, bbox_inches="tight")
    return fig


def print_patient_explanation(explanation: dict) -> None:
    """Pretty-print a single patient explanation to console."""
    print(f"\n  {explanation['patient']}:")
    print(f"    Prediction:  {explanation['prediction']} (prob={explanation['probability']:.3f})")
    print(f"    Base rate:   {explanation['base_rate']:.3f}")
    print(f"    Feature contributions:")
    for c in explanation["contributions"]:
        arrow = "+" if c["shap_value"] > 0 else ""
        print(f"      {c['feature']:20s} = {c['value']:>10.2f}  →  {arrow}{c['shap_value']:.4f} "
              f"({c['direction']} sepsis risk)")
