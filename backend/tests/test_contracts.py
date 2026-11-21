# -*- coding: utf-8 -*-
"""
Drift control para el contrato de API (backend/contracts/openapi.json).

Chequeos reales ejecutables:
  - `test_contract_openapi_file_exists`: el contrato existe (`backend/contracts/openapi.json`).
  - `test_contract_openapi_has_minimum_paths`: abre contracts/openapi.json, imprime número
    de paths y aserta > 50.
  - `test_app_has_minimum_routes`: `from app.main import app; assert len(app.routes) >= 50; print(len(app.routes))`.
  - `test_contract_v1_paths_in_live_app`: drift control — cada path /api/v1 del contrato
    (v1 namespace único) debe existir en la app vivo (`app.main.app.routes`).
"""

import os

# Entorno de desarrollo mínimo para importar app.main (Settings().SECRET_KEY).
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!!!")
os.environ.setdefault("ENVIRONMENT", "development")

import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
OPENAPI_FILE = BACKEND_DIR / "contracts" / "openapi.json"

MIN_CONTRACT_PATHS = 50
MIN_APP_ROUTES = 50


def _contract():
    return json.loads(OPENAPI_FILE.read_text(encoding="utf-8"))


def test_contract_openapi_file_exists():
    assert OPENAPI_FILE.is_file(), f"falta el contrato: {OPENAPI_FILE}"


def test_contract_openapi_has_minimum_paths():
    data = _contract()
    paths = data.get("paths", {})
    print(f"[contract] paths en contracts/openapi.json: {len(paths)}")
    assert len(paths) > MIN_CONTRACT_PATHS, f"contrato tiene {len(paths)} paths; esperado > {MIN_CONTRACT_PATHS}"


def test_contract_openapi_is_valid():
    data = _contract()
    assert isinstance(data, dict), "contrato no es un objeto JSON"
    assert isinstance(data.get("paths", {}), dict), "contrato sin 'paths'"


def test_app_has_minimum_routes():
    from app.main import app
    print(f"[app] routers registrados en app.main.app: {len(app.routes)}")
    assert len(app.routes) >= MIN_APP_ROUTES


def test_contract_v1_paths_in_live_app():
    """Drift control: paths /api/v1 del contrato deben existir en la app vivo."""
    data = _contract()
    contract_v1 = sorted(p for p in data.get("paths", {}) if p.startswith("/api/v1"))
    from app.main import app
    live_v1 = {getattr(r, "path", "") for r in app.routes if getattr(r, "path", "").startswith("/api/v1")}
    print(f"[drift] paths /api/v1 en contrato: {len(contract_v1)}; routers live /api/v1: {len(live_v1)}")
    missing = [p for p in contract_v1 if p not in live_v1]
    assert not missing, f"drift: {len(missing)} paths del contrato no existen en la app vivo: {missing[:5]}"
