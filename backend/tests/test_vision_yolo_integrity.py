# -*- coding: utf-8 -*-
"""SEC-FIX-006: el modelo YOLO debe verificarse antes de torch.load."""

import hashlib

import pytest

from app.core.config import settings
from app.services.vision.yolo_loader import YOLOLoader

PAYLOAD = b"fake-yolo-weights"
SHA = hashlib.sha256(PAYLOAD).hexdigest()


@pytest.fixture
def model_file(tmp_path):
    path = tmp_path / "yolov8n.pt"
    path.write_bytes(PAYLOAD)
    return path


class TestYoloIntegrity:
    def test_accepts_pinned_hash(self, model_file, monkeypatch):
        monkeypatch.setattr(settings, "YOLO_MODEL_SHA256", SHA, raising=False)
        YOLOLoader()._verify_integrity(model_file)

    def test_rejects_tampered_artifact(self, model_file, monkeypatch):
        monkeypatch.setattr(settings, "YOLO_MODEL_SHA256", "0" * 64, raising=False)
        with pytest.raises(RuntimeError, match="integrity check failed"):
            YOLOLoader()._verify_integrity(model_file)

    def test_production_requires_hash(self, model_file, monkeypatch):
        monkeypatch.setattr(settings, "YOLO_MODEL_SHA256", "", raising=False)
        monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)
        with pytest.raises(RuntimeError, match="YOLO_MODEL_SHA256 es obligatorio"):
            YOLOLoader()._verify_integrity(model_file)

    def test_development_allows_unpinned(self, model_file, monkeypatch):
        monkeypatch.setattr(settings, "YOLO_MODEL_SHA256", "", raising=False)
        monkeypatch.setattr(settings, "ENVIRONMENT", "development", raising=False)
        YOLOLoader()._verify_integrity(model_file)

    def test_production_disables_auto_download(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)
        assert YOLOLoader()._download(tmp_path / "missing.pt") is False
