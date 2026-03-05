"""Dataset management and simulation blueprint."""

import json
from pathlib import Path

import pandas as pd
from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, send_file, current_app,
)

datasets_bp = Blueprint("datasets", __name__)


def _list_datasets():
    """List all CSV datasets in the data directory."""
    from app import REPO_ROOT
    data_dir = REPO_ROOT / "data"
    datasets = []
    for csv_path in sorted(data_dir.glob("*.csv")):
        try:
            df = pd.read_csv(csv_path, nrows=1)
            n_rows = sum(1 for _ in open(csv_path)) - 1
            datasets.append({
                "name": csv_path.stem,
                "filename": csv_path.name,
                "rows": n_rows,
                "columns": len(df.columns),
                "size_kb": round(csv_path.stat().st_size / 1024, 1),
            })
        except Exception:
            continue
    return datasets


@datasets_bp.route("/")
def list_datasets():
    datasets = _list_datasets()
    return render_template("datasets/list.html", datasets=datasets)


@datasets_bp.route("/<name>")
def viewer(name):
    from app import REPO_ROOT
    data_dir = REPO_ROOT / "data"
    csv_path = data_dir / f"{name}.csv"
    if not csv_path.exists():
        flash(f"Dataset '{name}' not found.", "danger")
        return redirect(url_for("datasets.list_datasets"))

    page = int(request.args.get("page", 1))
    per_page = 50
    skip = (page - 1) * per_page

    df = pd.read_csv(csv_path)
    total_rows = len(df)
    total_pages = max(1, (total_rows + per_page - 1) // per_page)
    page_df = df.iloc[skip:skip + per_page]

    # Column stats
    stats = {}
    for col in df.select_dtypes(include="number").columns:
        stats[col] = {
            "mean": round(df[col].mean(), 2),
            "std": round(df[col].std(), 2),
            "min": round(df[col].min(), 2),
            "max": round(df[col].max(), 2),
        }

    # Class distribution
    class_dist = {}
    if "clinical_status" in df.columns:
        class_dist = df["clinical_status"].value_counts().to_dict()

    table_html = page_df.to_html(
        classes="table table-sm table-striped table-hover", index=False, border=0,
    )

    return render_template(
        "datasets/viewer.html",
        name=name,
        table_html=table_html,
        total_rows=total_rows,
        page=page,
        total_pages=total_pages,
        stats=stats,
        class_dist=class_dist,
    )


@datasets_bp.route("/<name>/download")
def download(name):
    from app import REPO_ROOT
    data_dir = REPO_ROOT / "data"
    csv_path = data_dir / f"{name}.csv"
    if not csv_path.exists():
        flash(f"Dataset '{name}' not found.", "danger")
        return redirect(url_for("datasets.list_datasets"))
    return send_file(csv_path, as_attachment=True, download_name=f"{name}.csv")


@datasets_bp.route("/simulate", methods=["POST"])
def simulate():
    from simulate_urine_biomarkers import simulate_dataset
    from app import REPO_ROOT

    n_septic = int(request.form.get("n_septic", 200))
    n_sirs = int(request.form.get("n_sirs", 150))
    n_healthy = int(request.form.get("n_healthy", 150))
    profile = request.form.get("profile", "general")
    noise = request.form.get("noise", "medium")
    extended = "extended" in request.form
    seed = int(request.form.get("seed", 42))

    total = n_septic + n_sirs + n_healthy
    if total > 50000:
        flash("Maximum 50,000 samples allowed.", "warning")
        return redirect(url_for("datasets.list_datasets"))

    try:
        df = simulate_dataset(
            n_septic=n_septic,
            n_sirs=n_sirs,
            n_healthy=n_healthy,
            profile_name=profile,
            noise=noise,
            extended=extended,
            seed=seed,
        )

        filename = f"simulated_{total}_{profile}"
        data_dir = REPO_ROOT / "data"
        data_dir.mkdir(exist_ok=True)
        csv_path = data_dir / f"{filename}.csv"
        df.to_csv(csv_path, index=False)

        flash(f"Generated {total} samples: {csv_path.name}", "success")
        return redirect(url_for("datasets.viewer", name=filename))

    except Exception as e:
        flash(f"Simulation error: {e}", "danger")
        return redirect(url_for("datasets.list_datasets"))
