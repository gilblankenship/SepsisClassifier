"""JSON API endpoints."""

from flask import Blueprint, jsonify, request
import numpy as np

api_bp = Blueprint("api", __name__)


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "sepsis-dx"})


@api_bp.route("/predict", methods=["POST"])
def predict_json():
    from sepsis.model_export import SepsisPredictor
    from app import get_active_model

    data = request.get_json(force=True)
    crp_cr = float(data.get("crp_cr", 0))
    ip10_cr = float(data.get("ip10_cr", 0))
    model_name = data.get("model_name") or get_active_model()

    try:
        predictor = SepsisPredictor.from_exported(model_name)
        result = predictor.predict_sample(crp_cr=crp_cr, ip10_cr=ip10_cr)
        return jsonify(result)
    except FileNotFoundError:
        return jsonify({"error": f"Model '{model_name}' not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/models")
def list_models():
    from sepsis.model_export import list_exported_models
    return jsonify(list_exported_models())
