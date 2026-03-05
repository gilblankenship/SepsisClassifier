"""Background training job worker using threading."""

import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

_jobs: dict = {}
_lock = threading.Lock()


@dataclass
class TrainingJob:
    job_id: str
    status: str = "pending"
    progress: int = 0
    message: str = ""
    cv_results: list = field(default_factory=list)
    model_names: list = field(default_factory=list)
    error: str = ""
    started_at: float = 0.0
    finished_at: float = 0.0
    dataset_name: str = ""

    def to_dict(self) -> dict:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "cv_results": self.cv_results,
            "model_names": self.model_names,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "elapsed": round(time.time() - self.started_at, 1) if self.started_at else 0,
            "dataset_name": self.dataset_name,
        }


def submit_job(
    classifiers: dict[str, Any],
    dataset_path: str,
    feature_mode: str = "basic",
) -> str:
    job_id = str(uuid.uuid4())[:8]
    job = TrainingJob(
        job_id=job_id,
        dataset_name=Path(dataset_path).stem,
    )
    with _lock:
        _jobs[job_id] = job
    t = threading.Thread(
        target=_run_training,
        args=(job_id, classifiers, dataset_path, feature_mode),
        daemon=True,
    )
    t.start()
    return job_id


def get_job(job_id: str) -> TrainingJob | None:
    return _jobs.get(job_id)


def _run_training(job_id: str, classifiers: dict, dataset_path: str, feature_mode: str):
    from sepsis.data import load_csv, get_features_and_labels
    from sepsis.features import add_engineered_features, FEATURE_COLS_EXTENDED
    from sepsis.evaluation import compare_models, compute_metrics
    from sepsis.model_export import export_all_models
    from sepsis.tuning import optimize_threshold

    job = _jobs[job_id]
    job.status = "running"
    job.started_at = time.time()

    try:
        job.message = "Loading dataset..."
        job.progress = 5
        df = load_csv(dataset_path)
        X, y = get_features_and_labels(df)

        if feature_mode == "extended":
            df = add_engineered_features(df)
            X = df[FEATURE_COLS_EXTENDED].values

        job.message = "Running cross-validation..."
        job.progress = 15

        cv_df = compare_models(classifiers, X, y, n_splits=5)
        job.cv_results = cv_df.to_dict(orient="records")
        job.progress = 60

        job.message = "Optimizing thresholds..."
        job.progress = 65
        feature_names = ["crp_cr_pg_mg", "ip10_cr_pg_mg"]
        thresholds = {}
        for name, clf in classifiers.items():
            try:
                clf.fit(X, y)
                y_prob = clf.predict_proba(X)[:, 1]
                opt = optimize_threshold(y, y_prob, strategy="max_youden")
                thresholds[name] = opt["optimal_threshold"]
            except Exception:
                thresholds[name] = 0.5

        job.message = "Exporting models..."
        job.progress = 80
        paths = export_all_models(classifiers, X, y, feature_names, thresholds)
        job.model_names = [p.stem for p in paths]

        job.status = "complete"
        job.progress = 100
        job.message = f"Training complete. {len(paths)} models exported."

    except Exception as e:
        job.status = "error"
        job.error = str(e)
        job.message = f"Error: {e}"

    finally:
        job.finished_at = time.time()
