"""Model management blueprint."""

import json
from pathlib import Path

from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, session, current_app,
)

models_bp = Blueprint("models_bp", __name__)


@models_bp.route("/")
def list_models():
    from sepsis.model_export import list_exported_models
    from app import get_active_model

    models = list_exported_models()
    active = get_active_model()
    return render_template("models/list.html", models=models, active_model=active)


@models_bp.route("/<name>")
def detail(name):
    from sepsis.model_export import MODELS_DIR

    meta_path = MODELS_DIR / f"{name}_meta.json"
    if not meta_path.exists():
        flash(f"Model '{name}' not found.", "danger")
        return redirect(url_for("models_bp.list_models"))

    with open(meta_path) as f:
        meta = json.load(f)

    model_path = MODELS_DIR / f"{name}.pkl"
    file_size = model_path.stat().st_size if model_path.exists() else 0

    return render_template("models/detail.html", meta=meta, name=name, file_size=file_size)


@models_bp.route("/<name>/activate", methods=["POST"])
def activate(name):
    from sepsis.model_export import MODELS_DIR

    model_path = MODELS_DIR / f"{name}.pkl"
    if not model_path.exists():
        flash(f"Model '{name}' not found.", "danger")
    else:
        session["active_model"] = name
        flash(f"Active model set to '{name}'.", "success")

    return redirect(url_for("models_bp.list_models"))


@models_bp.route("/<name>/delete", methods=["POST"])
def delete(name):
    from sepsis.model_export import MODELS_DIR
    from app import get_active_model

    if name == get_active_model():
        flash("Cannot delete the active model. Activate a different model first.", "warning")
        return redirect(url_for("models_bp.list_models"))

    pkl_path = MODELS_DIR / f"{name}.pkl"
    meta_path = MODELS_DIR / f"{name}_meta.json"

    deleted = False
    if pkl_path.exists():
        pkl_path.unlink()
        deleted = True
    if meta_path.exists():
        meta_path.unlink()
        deleted = True

    if deleted:
        flash(f"Model '{name}' deleted.", "success")
    else:
        flash(f"Model '{name}' not found.", "danger")

    return redirect(url_for("models_bp.list_models"))
