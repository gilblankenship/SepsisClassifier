"""SepsisDx Web Application — Flask app factory."""

import os
import sys
from pathlib import Path

# Add repo root to sys.path so 'import sepsis' works
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "data_simulator"))

import matplotlib
matplotlib.use("Agg")

from flask import Flask, render_template, session
from flask_cors import CORS


def get_active_model() -> str:
    """Get the currently active model name."""
    from flask import current_app
    return session.get(
        "active_model",
        current_app.config.get("ACTIVE_MODEL", "random_forest"),
    )


def create_app(config_override=None) -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-insecure-key-change-in-production")
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
    app.config["UPLOAD_FOLDER"] = str(Path(__file__).parent / "uploads")
    app.config["MODELS_DIR"] = str(REPO_ROOT / "models")
    app.config["DATA_DIR"] = str(REPO_ROOT / "data")
    app.config["ACTIVE_MODEL"] = os.environ.get("ACTIVE_MODEL", "random_forest")

    if config_override:
        app.config.update(config_override)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app)

    # Register blueprints
    from blueprints.predict import predict_bp
    from blueprints.batch import batch_bp
    from blueprints.train import train_bp
    from blueprints.models_bp import models_bp
    from blueprints.explain import explain_bp
    from blueprints.datasets import datasets_bp
    from blueprints.api import api_bp
    from blueprints.help import help_bp

    app.register_blueprint(predict_bp, url_prefix="/predict")
    app.register_blueprint(batch_bp, url_prefix="/batch")
    app.register_blueprint(train_bp, url_prefix="/train")
    app.register_blueprint(models_bp, url_prefix="/models")
    app.register_blueprint(explain_bp, url_prefix="/explain")
    app.register_blueprint(datasets_bp, url_prefix="/datasets")
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(help_bp, url_prefix="/help")

    # Make get_active_model available in templates
    app.jinja_env.globals["get_active_model"] = get_active_model

    @app.route("/")
    def index():
        from sepsis.model_export import list_exported_models
        models = list_exported_models()
        active = get_active_model()
        return render_template("index.html", models=models, active_model=active)

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)
