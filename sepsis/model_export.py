"""Model export, import, and prediction API for sepsis classifiers."""

from __future__ import annotations

import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from sepsis.evaluation import compute_metrics

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def ensure_models_dir() -> Path:
    MODELS_DIR.mkdir(exist_ok=True)
    return MODELS_DIR


def export_model(
    classifier: Any,
    model_name: str,
    feature_names: list[str],
    train_metrics: dict | None = None,
    threshold: float = 0.5,
    metadata: dict | None = None,
) -> Path:
    """Export a trained classifier to disk with metadata.

    Saves:
    - <model_name>.pkl  — serialized classifier
    - <model_name>_meta.json — metadata, features, metrics, threshold
    """
    ensure_models_dir()

    # Save model
    model_path = MODELS_DIR / f"{model_name}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(classifier, f)

    # Save metadata
    meta = {
        "model_name": model_name,
        "model_class": classifier.__class__.__name__,
        "model_params": classifier.get_params(),
        "feature_names": feature_names,
        "optimal_threshold": threshold,
        "exported_at": datetime.now().isoformat(),
        "gold_standard": "Blood culture + Sepsis-3 (SOFA >= 2)",
        "biomarker_source": "Urine ELISA",
    }
    if train_metrics:
        # Convert numpy types to native Python for JSON
        meta["train_metrics"] = {
            k: float(v) if isinstance(v, (np.floating, float)) else v
            for k, v in train_metrics.items()
        }
    if metadata:
        meta.update(metadata)

    meta_path = MODELS_DIR / f"{model_name}_meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, default=str)

    return model_path


def load_model(model_name: str) -> tuple[Any, dict]:
    """Load a previously exported classifier and its metadata.

    Returns:
        (classifier, metadata_dict)
    """
    model_path = MODELS_DIR / f"{model_name}.pkl"
    meta_path = MODELS_DIR / f"{model_name}_meta.json"

    if not model_path.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    with open(model_path, "rb") as f:
        classifier = pickle.load(f)

    meta = {}
    if meta_path.exists():
        with open(meta_path, "r") as f:
            meta = json.load(f)

    return classifier, meta


def list_exported_models() -> list[dict]:
    """List all exported models with their metadata summaries."""
    ensure_models_dir()
    models = []
    for meta_path in sorted(MODELS_DIR.glob("*_meta.json")):
        with open(meta_path, "r") as f:
            meta = json.load(f)
        models.append({
            "name": meta.get("model_name"),
            "class": meta.get("model_class"),
            "threshold": meta.get("optimal_threshold"),
            "exported_at": meta.get("exported_at"),
            "auroc": meta.get("train_metrics", {}).get("auroc"),
        })
    return models


class SepsisPredictor:
    """High-level prediction API for clinical use.

    Wraps a trained classifier with preprocessing, threshold application,
    and human-readable output.

    Usage:
        predictor = SepsisPredictor.from_exported("random_forest_best")
        result = predictor.predict_sample(crp_cr=450.0, ip10_cr=85.0)
        print(result)
    """

    def __init__(self, classifier: Any, metadata: dict):
        self.classifier = classifier
        self.metadata = metadata
        self.threshold = metadata.get("optimal_threshold", 0.5)
        self.feature_names = metadata.get("feature_names", ["crp_cr_pg_mg", "ip10_cr_pg_mg"])

    @classmethod
    def from_exported(cls, model_name: str) -> "SepsisPredictor":
        """Load a predictor from an exported model."""
        classifier, meta = load_model(model_name)
        return cls(classifier, meta)

    def predict_sample(
        self,
        crp_cr: float,
        ip10_cr: float,
        threshold: float | None = None,
    ) -> dict:
        """Predict sepsis status for a single urine sample.

        Args:
            crp_cr: CRP/Creatinine ratio (pg/mg)
            ip10_cr: IP-10/Creatinine ratio (pg/mg)
            threshold: Override classification threshold

        Returns:
            Dict with prediction, probability, risk level, and clinical context.
        """
        t = threshold or self.threshold
        X = np.array([[crp_cr, ip10_cr]])

        prob = self.classifier.predict_proba(X)[0, 1]
        prediction = int(prob >= t)

        # Risk stratification
        if prob < 0.2:
            risk_level = "LOW"
        elif prob < 0.5:
            risk_level = "MODERATE"
        elif prob < 0.8:
            risk_level = "HIGH"
        else:
            risk_level = "VERY HIGH"

        # SepsisDx comparison
        sepsisdx_result = "Septic" if (crp_cr > 300 or ip10_cr > 100) else "Not Septic"

        return {
            "prediction": "Septic" if prediction == 1 else "Not Septic",
            "probability": round(float(prob), 4),
            "risk_level": risk_level,
            "threshold_used": t,
            "model": self.metadata.get("model_name", "unknown"),
            "input": {"crp_cr_pg_mg": crp_cr, "ip10_cr_pg_mg": ip10_cr},
            "sepsisdx_comparison": sepsisdx_result,
            "clinical_note": _clinical_note(prob, crp_cr, ip10_cr, risk_level),
        }

    def predict_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Predict sepsis status for a batch of samples.

        Args:
            df: DataFrame with columns crp_cr_pg_mg, ip10_cr_pg_mg

        Returns:
            DataFrame with added prediction columns.
        """
        X = df[["crp_cr_pg_mg", "ip10_cr_pg_mg"]].values
        probs = self.classifier.predict_proba(X)[:, 1]
        preds = (probs >= self.threshold).astype(int)

        result = df.copy()
        result["ml_probability"] = probs
        result["ml_prediction"] = np.where(preds == 1, "Septic", "Not Septic")
        result["ml_risk_level"] = pd.cut(
            probs,
            bins=[0, 0.2, 0.5, 0.8, 1.0],
            labels=["LOW", "MODERATE", "HIGH", "VERY HIGH"],
        )
        # SepsisDx comparison
        result["sepsisdx_prediction"] = np.where(
            (X[:, 0] > 300) | (X[:, 1] > 100), "Septic", "Not Septic"
        )
        result["models_agree"] = result["ml_prediction"] == result["sepsisdx_prediction"]
        return result


def _clinical_note(prob: float, crp_cr: float, ip10_cr: float, risk_level: str) -> str:
    """Generate a brief clinical context note."""
    notes = []
    if risk_level in ("HIGH", "VERY HIGH"):
        notes.append("Consider blood culture and empiric antibiotics per Sepsis-3 guidelines.")
    if crp_cr > 300 and ip10_cr > 100:
        notes.append("Both biomarkers elevated — strong sepsis signal.")
    elif crp_cr > 300:
        notes.append("CRP/Cr elevated; IP-10/Cr within range.")
    elif ip10_cr > 100:
        notes.append("IP-10/Cr elevated; CRP/Cr within range.")
    elif prob > 0.5:
        notes.append("ML model detects sepsis pattern despite both markers below SepsisDx thresholds — borderline case.")
    else:
        notes.append("Biomarkers within normal range.")
    return " ".join(notes)


def export_all_models(
    classifiers: dict[str, Any],
    X: np.ndarray,
    y: np.ndarray,
    feature_names: list[str],
    thresholds: dict[str, float] | None = None,
) -> list[Path]:
    """Train, evaluate, and export all classifiers."""
    paths = []
    for name, clf in classifiers.items():
        clf.fit(X, y)
        y_pred = clf.predict(X)
        y_prob = clf.predict_proba(X)[:, 1]
        metrics = compute_metrics(y, y_pred, y_prob)

        safe_name = name.lower().replace(" ", "_").replace("(", "").replace(")", "")
        threshold = thresholds.get(name, 0.5) if thresholds else 0.5

        path = export_model(
            clf,
            model_name=safe_name,
            feature_names=feature_names,
            train_metrics=metrics,
            threshold=threshold,
        )
        paths.append(path)
        print(f"  Exported: {safe_name} (AUROC={metrics.get('auroc', 'N/A'):.4f}, threshold={threshold})")

    return paths
