# -*- coding: utf-8 -*-
"""Matriz de enforcement de clearance sobre las rutas realmente montadas.

Regresión de ADR-010 (clearance hierarchy leak reduction). Inspecciona el
árbol de dependencias de `app.main.app` — no una copia de test — para
garantizar que ninguna ruta viva de `/api/v1` o `/api/v3` quede accesible
"solo autenticada" (lo que permitiría a un usuario OPEN leer datos
clasificados).
"""

import pytest
from fastapi.routing import APIRoute

from app.main import app

# Rutas públicas por diseño: health para probes y auth para el propio login.
PUBLIC_PREFIXES = ("/api/v1/health", "/api/v1/auth")


def _dependency_calls(dependant) -> list[tuple[str, str]]:
    acc: list[tuple[str, str]] = []
    stack = [dependant]
    while stack:
        node = stack.pop()
        for sub in node.dependencies:
            fn = sub.call
            acc.append((getattr(fn, "__module__", ""), getattr(fn, "__qualname__", "")))
            stack.append(sub)
    return acc


def _live_routes():
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.path.startswith(("/api/v1", "/api/v3")):
            continue
        if route.path.startswith(PUBLIC_PREFIXES):
            continue
        yield route


def _requires_clearance(route: APIRoute) -> bool:
    calls = _dependency_calls(route.dependant)
    return any(
        "clearance" in qualname or "operator_key" in qualname
        for _module, qualname in calls
    )


def test_matrix_has_routes():
    """La introspección debe ver rutas: un fallo aquí invalida el resto."""
    assert len(list(_live_routes())) >= 100


def test_every_live_v1_v3_route_declares_clearance():
    offenders = [
        f"{sorted(route.methods)} {route.path}"
        for route in _live_routes()
        if not _requires_clearance(route)
    ]
    assert offenders == [], (
        "Rutas accesibles sin clearance (ADR-010): " + ", ".join(offenders)
    )


def test_health_and_auth_stay_public():
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    assert "/api/v1/health" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/auth/refresh" in paths


def test_v3_coa_is_clearance_guarded():
    """/api/v3/coa expone cursos de acción y disponibilidad de armas."""
    coa_routes = [
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path.startswith("/api/v3/coa")
    ]
    assert coa_routes, "El router COA v3 debe estar montado"
    for route in coa_routes:
        assert _requires_clearance(route), f"COA sin clearance: {route.path}"


def test_media_dead_router_not_exposed():
    """v1/media.py existe pero no se monta; si se monta debe llevar clearance.

    Se documenta el estado real para detectar un montaje accidental sin
    enforcement (el PUT presigned no exigía clearance por diseño HMAC).
    """
    for route in app.routes:
        if isinstance(route, APIRoute) and route.path.startswith("/api/v1/media"):
            assert _requires_clearance(route), f"Media montado sin clearance: {route.path}"
