"""Single patient prediction blueprint."""

from flask import Blueprint, render_template, request, flash, redirect, url_for
import numpy as np

predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/")
def form():
    from sepsis.model_export import list_exported_models
    models = list_exported_models()
    return render_template("predict/single.html", models=models)


@predict_bp.route("/run", methods=["POST"])
def run_prediction():
    from sepsis.model_export import SepsisPredictor, load_model, list_exported_models
    from sepsis.explainability import explain_single_patient
    from sepsis.data import load_reference_samples, get_features_and_labels
    from app import get_active_model
    import pandas as pd
    from pathlib import Path

    try:
        crp_cr = float(request.form["crp_cr"])
        ip10_cr = float(request.form["ip10_cr"])
    except (ValueError, KeyError):
        flash("Please enter valid numeric values for both biomarkers.", "danger")
        return redirect(url_for("predict.form"))

    model_name = request.form.get("model_name") or get_active_model()

    try:
        predictor = SepsisPredictor.from_exported(model_name)
        result = predictor.predict_sample(crp_cr=crp_cr, ip10_cr=ip10_cr)
    except FileNotFoundError:
        flash(f"Model '{model_name}' not found. Please export models first.", "danger")
        return redirect(url_for("predict.form"))

    # SHAP explanation
    shap_data = None
    try:
        clf, meta = load_model(model_name)
        # Load background data
        from app import REPO_ROOT
        data_dir = REPO_ROOT / "data"
        bg_files = sorted(data_dir.glob("simulated_*.csv"), reverse=True)
        if bg_files:
            bg_df = pd.read_csv(bg_files[0])
            X_bg = bg_df[["crp_cr_pg_mg", "ip10_cr_pg_mg"]].values[:100]
        else:
            ref_df = load_reference_samples()
            X_bg, _ = get_features_and_labels(ref_df)

        patient = np.array([crp_cr, ip10_cr])
        feature_names = ["CRP/Cr", "IP-10/Cr"]
        shap_result = explain_single_patient(
            clf, patient, feature_names, X_bg, "Patient"
        )
        shap_data = shap_result["contributions"]
    except Exception:
        pass  # SHAP is optional, don't fail the prediction

    models = list_exported_models()
    return render_template(
        "predict/result.html",
        result=result,
        shap_data=shap_data,
        models=models,
        selected_model=model_name,
    )
