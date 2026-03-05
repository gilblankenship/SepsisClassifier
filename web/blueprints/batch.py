"""Batch CSV prediction blueprint."""

import io
import uuid
from pathlib import Path

import pandas as pd
from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, send_file, current_app,
)
from werkzeug.utils import secure_filename

batch_bp = Blueprint("batch", __name__)


@batch_bp.route("/")
def upload_form():
    return render_template("batch/upload.html")


@batch_bp.route("/upload", methods=["POST"])
def upload_csv():
    from sepsis.model_export import SepsisPredictor
    from app import get_active_model

    if "csv_file" not in request.files:
        flash("No file uploaded.", "danger")
        return redirect(url_for("batch.upload_form"))

    file = request.files["csv_file"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("batch.upload_form"))

    if not file.filename.lower().endswith(".csv"):
        flash("Please upload a CSV file.", "danger")
        return redirect(url_for("batch.upload_form"))

    try:
        content = file.read().decode("utf-8")
        df = pd.read_csv(io.StringIO(content))
    except Exception as e:
        flash(f"Error reading CSV: {e}", "danger")
        return redirect(url_for("batch.upload_form"))

    # Validate required columns
    required = {"crp_cr_pg_mg", "ip10_cr_pg_mg"}
    if not required.issubset(set(df.columns)):
        flash(
            f"CSV must contain columns: {', '.join(required)}. "
            f"Found: {', '.join(df.columns[:10])}",
            "danger",
        )
        return redirect(url_for("batch.upload_form"))

    model_name = request.form.get("model_name") or get_active_model()
    try:
        predictor = SepsisPredictor.from_exported(model_name)
        result_df = predictor.predict_batch(df)
    except FileNotFoundError:
        flash(f"Model '{model_name}' not found.", "danger")
        return redirect(url_for("batch.upload_form"))

    # Save results
    job_id = str(uuid.uuid4())[:8]
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    result_path = upload_dir / f"batch_{job_id}.csv"
    result_df.to_csv(result_path, index=False)

    # Summary stats
    n_total = len(result_df)
    n_septic = (result_df["ml_prediction"] == "Septic").sum()
    n_not_septic = n_total - n_septic
    agreement = result_df["models_agree"].mean() * 100 if "models_agree" in result_df.columns else None

    # Show first 100 rows in table
    display_df = result_df.head(100)
    display_cols = [c for c in [
        "crp_cr_pg_mg", "ip10_cr_pg_mg", "ml_prediction",
        "ml_probability", "ml_risk_level", "sepsisdx_prediction", "models_agree",
    ] if c in display_df.columns]

    return render_template(
        "batch/results.html",
        job_id=job_id,
        n_total=n_total,
        n_septic=int(n_septic),
        n_not_septic=int(n_not_septic),
        agreement=agreement,
        table_html=display_df[display_cols].to_html(
            classes="table table-sm table-striped", index=False, border=0,
        ),
        model_name=model_name,
    )


@batch_bp.route("/download/<job_id>")
def download(job_id):
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    result_path = upload_dir / f"batch_{secure_filename(job_id)}.csv"
    if not result_path.exists():
        flash("Results file not found.", "danger")
        return redirect(url_for("batch.upload_form"))
    return send_file(result_path, as_attachment=True, download_name=f"sepsis_predictions_{job_id}.csv")
