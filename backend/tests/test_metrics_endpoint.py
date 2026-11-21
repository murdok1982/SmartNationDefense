# -*- coding: utf-8 -*-
"""SEC-FIX-007: /metrics expone datos operativos y admite token."""

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


class TestMetricsEndpoint:
    def test_metrics_is_prometheus_text(self, monkeypatch):
        monkeypatch.setattr(settings, "METRICS_TOKEN", "", raising=False)
        response = TestClient(app).get("/metrics")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")
        assert "sesis_http_requests_total" in response.text or "sesis_module_up" in response.text

    def test_metrics_rejects_missing_token(self, monkeypatch):
        monkeypatch.setattr(settings, "METRICS_TOKEN", "s3cret-metrics", raising=False)
        response = TestClient(app).get("/metrics")
        assert response.status_code == 401

    def test_metrics_accepts_x_metrics_token(self, monkeypatch):
        monkeypatch.setattr(settings, "METRICS_TOKEN", "s3cret-metrics", raising=False)
        response = TestClient(app).get(
            "/metrics", headers={"X-Metrics-Token": "s3cret-metrics"}
        )
        assert response.status_code == 200

    def test_metrics_accepts_bearer(self, monkeypatch):
        monkeypatch.setattr(settings, "METRICS_TOKEN", "s3cret-metrics", raising=False)
        response = TestClient(app).get(
            "/metrics", headers={"Authorization": "Bearer s3cret-metrics"}
        )
        assert response.status_code == 200
