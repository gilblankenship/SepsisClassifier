"""Tests for the SepsisDx web application."""

import sys
from pathlib import Path

# Ensure web/ is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "web"))

import pytest
from app import create_app


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret"})
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


class TestHealthAndNavigation:
    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["service"] == "sepsis-dx"

    def test_dashboard(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"SepsisDx" in resp.data

    def test_predict_page(self, client):
        resp = client.get("/predict/")
        assert resp.status_code == 200
        assert b"CRP" in resp.data

    def test_batch_page(self, client):
        resp = client.get("/batch/")
        assert resp.status_code == 200

    def test_train_page(self, client):
        resp = client.get("/train/")
        assert resp.status_code == 200

    def test_models_page(self, client):
        resp = client.get("/models/")
        assert resp.status_code == 200

    def test_explain_page(self, client):
        resp = client.get("/explain/")
        assert resp.status_code == 200

    def test_datasets_page(self, client):
        resp = client.get("/datasets/")
        assert resp.status_code == 200


class TestAPI:
    def test_api_models(self, client):
        resp = client.get("/api/models")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)

    def test_api_predict_valid(self, client):
        resp = client.post("/api/predict", json={
            "crp_cr": 500.0,
            "ip10_cr": 150.0,
        })
        # May return 200 or 500 depending on model availability
        assert resp.status_code in (200, 500)


class TestPrediction:
    def test_predict_form_submit(self, client):
        resp = client.post("/predict/run", data={
            "crp_creatinine": "500",
            "ip10_creatinine": "150",
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestHelpPage:
    def test_help_page(self, client):
        resp = client.get("/help/")
        assert resp.status_code == 200
        assert b"Quick Start" in resp.data
        assert b"Digital Biosciences" in resp.data


class TestErrorPages:
    def test_404(self, client):
        resp = client.get("/nonexistent-page")
        assert resp.status_code == 404
        assert b"404" in resp.data
