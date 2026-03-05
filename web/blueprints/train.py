"""Model training blueprint with background job support."""

from pathlib import Path

from flask import (
    Blueprint, render_template, request, flash, redirect,
    url_for, jsonify, current_app,
)

train_bp = Blueprint("train", __name__)

CLASSIFIER_REGISTRY = {
    "sepsisdx": ("SepsisDx (Baseline)", {}),
    "logistic": ("Logistic Regression", {"C": 1.0, "class_weight": "balanced"}),
    "random_forest": ("Random Forest", {"n_estimators": 200, "max_depth": 5, "class_weight": "balanced"}),
    "xgboost": ("XGBoost", {"n_estimators": 200, "max_depth": 4, "learning_rate": 0.1}),
    "neural_network": ("Neural Network", {"hidden_layers": (32, 16, 8), "max_iter": 500}),
}


def _list_datasets():
    from app import REPO_ROOT
    data_dir = REPO_ROOT / "data"
    datasets = []
    for f in sorted(data_dir.glob("*.csv")):
        datasets.append({"name": f.stem, "path": str(f)})
    return datasets


@train_bp.route("/")
def configure():
    datasets = _list_datasets()
    return render_template(
        "train/configure.html",
        classifiers=CLASSIFIER_REGISTRY,
        datasets=datasets,
    )


@train_bp.route("/start", methods=["POST"])
def start():
    from sepsis.classifiers import (
        SepsisDxClassifier, LogisticSepsisClassifier,
        RandomForestSepsisClassifier, XGBoostSepsisClassifier,
        NeuralNetSepsisClassifier,
    )
    from tasks.training import submit_job

    selected = request.form.getlist("classifiers")
    if not selected:
        flash("Select at least one classifier.", "warning")
        return redirect(url_for("train.configure"))

    dataset = request.form.get("dataset")
    if not dataset:
        flash("Select a dataset.", "warning")
        return redirect(url_for("train.configure"))

    # Handle file upload
    if dataset == "__upload__" and "dataset_file" in request.files:
        file = request.files["dataset_file"]
        if file.filename:
            from app import REPO_ROOT
            import werkzeug.utils
            safe_name = werkzeug.utils.secure_filename(file.filename)
            upload_path = REPO_ROOT / "data" / safe_name
            file.save(str(upload_path))
            dataset = str(upload_path)
        else:
            flash("No file uploaded.", "warning")
            return redirect(url_for("train.configure"))

    # Build classifier dict
    cls_map = {
        "sepsisdx": SepsisDxClassifier,
        "logistic": LogisticSepsisClassifier,
        "random_forest": RandomForestSepsisClassifier,
        "xgboost": XGBoostSepsisClassifier,
        "neural_network": NeuralNetSepsisClassifier,
    }

    classifiers = {}
    for key in selected:
        if key in cls_map:
            _, default_params = CLASSIFIER_REGISTRY[key]
            # Parse form overrides
            params = {}
            for pname, pval in default_params.items():
                form_key = f"{key}_{pname}"
                if form_key in request.form:
                    raw = request.form[form_key]
                    if isinstance(pval, int):
                        params[pname] = int(raw)
                    elif isinstance(pval, float):
                        params[pname] = float(raw)
                    elif isinstance(pval, tuple):
                        cleaned = raw.strip("() ")
                        params[pname] = tuple(int(x.strip()) for x in cleaned.split(","))
                    else:
                        params[pname] = raw
                else:
                    params[pname] = pval

            name, _ = CLASSIFIER_REGISTRY[key]
            classifiers[name] = cls_map[key](**params)

    feature_mode = request.form.get("feature_mode", "basic")
    job_id = submit_job(classifiers, dataset, feature_mode)

    return redirect(url_for("train.progress", job_id=job_id))


@train_bp.route("/progress/<job_id>")
def progress(job_id):
    return render_template("train/progress.html", job_id=job_id)


@train_bp.route("/status/<job_id>")
def status(job_id):
    from tasks.training import get_job
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job.to_dict())


@train_bp.route("/results/<job_id>")
def results(job_id):
    from tasks.training import get_job
    job = get_job(job_id)
    if not job:
        flash("Training job not found.", "danger")
        return redirect(url_for("train.configure"))
    if job.status != "complete":
        return redirect(url_for("train.progress", job_id=job_id))
    return render_template("train/results.html", job=job.to_dict())
