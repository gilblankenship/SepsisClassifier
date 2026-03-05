"""Explainability dashboard blueprint — SHAP plots and decision boundaries."""

import io
import threading

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from flask import Blueprint, render_template, send_file, request, current_app
from pathlib import Path

explain_bp = Blueprint("explain", __name__)

_plot_lock = threading.Lock()


def _fig_to_response(fig):
    """Convert a matplotlib figure to a PNG Flask response."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    plt.close("all")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


def _load_background():
    """Load background data for SHAP and visualizations."""
    from app import REPO_ROOT
    data_dir = REPO_ROOT / "data"
    bg_files = sorted(data_dir.glob("simulated_*.csv"), reverse=True)
    if bg_files:
        df = pd.read_csv(bg_files[0])
    else:
        from sepsis.data import generate_synthetic_data
        df = generate_synthetic_data()

    X = df[["crp_cr_pg_mg", "ip10_cr_pg_mg"]].values
    y = df["gold_standard_label"].values if "gold_standard_label" in df.columns else None
    return X, y, df


@explain_bp.route("/")
def dashboard():
    from sepsis.model_export import list_exported_models
    from app import get_active_model
    models = list_exported_models()
    active = get_active_model()
    return render_template("explain/dashboard.html", models=models, active_model=active)


@explain_bp.route("/shap-summary.png")
def shap_summary_png():
    from sepsis.model_export import load_model
    from sepsis.explainability import compute_shap_tree, compute_shap_values, plot_shap_summary
    from app import get_active_model

    model_name = request.args.get("model", get_active_model())
    clf, meta = load_model(model_name)
    X, y, _ = _load_background()

    clf.fit(X, y)
    feature_names = ["CRP/Cr", "IP-10/Cr"]

    with _plot_lock:
        try:
            explanation = compute_shap_tree(clf, X, feature_names)
        except Exception:
            explanation = compute_shap_values(clf, X, feature_names, background_size=50)
        fig = plot_shap_summary(explanation, title=f"SHAP Summary -- {model_name}", save=False)
        fig = plt.gcf()
        return _fig_to_response(fig)


@explain_bp.route("/shap-bar.png")
def shap_bar_png():
    from sepsis.model_export import load_model
    from sepsis.explainability import compute_shap_tree, compute_shap_values, plot_shap_bar
    from app import get_active_model

    model_name = request.args.get("model", get_active_model())
    clf, meta = load_model(model_name)
    X, y, _ = _load_background()

    clf.fit(X, y)
    feature_names = ["CRP/Cr", "IP-10/Cr"]

    with _plot_lock:
        try:
            explanation = compute_shap_tree(clf, X, feature_names)
        except Exception:
            explanation = compute_shap_values(clf, X, feature_names, background_size=50)
        fig = plot_shap_bar(explanation, title=f"Mean |SHAP| -- {model_name}", save=False)
        return _fig_to_response(fig)


@explain_bp.route("/decision-boundary.png")
def decision_boundary_png():
    from sepsis.model_export import load_model
    from sepsis.visualization import plot_decision_boundary
    from app import get_active_model

    model_name = request.args.get("model", get_active_model())
    clf, meta = load_model(model_name)
    X, y, _ = _load_background()

    clf.fit(X, y)

    with _plot_lock:
        fig = plot_decision_boundary(
            clf, X, y,
            title=f"Decision Boundary -- {model_name}",
            save=False,
        )
        return _fig_to_response(fig)


@explain_bp.route("/roc-curves.png")
def roc_curves_png():
    from sepsis.model_export import load_model, list_exported_models
    from sepsis.visualization import plot_roc_curves
    from sepsis.evaluation import literature_benchmarks

    X, y, _ = _load_background()
    models_data = {}

    for m in list_exported_models():
        try:
            clf, meta = load_model(m["name"])
            clf.fit(X, y)
            y_prob = clf.predict_proba(X)[:, 1]
            models_data[m["name"]] = (y, y_prob)
        except Exception:
            continue

    benchmarks = literature_benchmarks()

    with _plot_lock:
        fig = plot_roc_curves(models_data, benchmarks, save=False)
        return _fig_to_response(fig)


@explain_bp.route("/calibration.png")
def calibration_png():
    from sepsis.model_export import load_model, list_exported_models
    from sepsis.visualization import plot_calibration_curves

    X, y, _ = _load_background()
    cal_data = {}

    for m in list_exported_models():
        try:
            clf, meta = load_model(m["name"])
            clf.fit(X, y)
            y_prob = clf.predict_proba(X)[:, 1]
            cal_data[m["name"]] = (y, y_prob)
        except Exception:
            continue

    with _plot_lock:
        fig = plot_calibration_curves(cal_data, save=False)
        return _fig_to_response(fig)
