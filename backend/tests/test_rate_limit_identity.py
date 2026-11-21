# -*- coding: utf-8 -*-
"""Regresión SEC-FIX-009/010 (re-auditoría FASE 3).

Dos bypasses detectados sobre los controles de rate-limit/lockout:

1. ``request.url.path`` se reconstruye desde el header ``Host``
   (CVE-2026-48710 "BadHost"): un Host con "/" antepone segmentos y cambia la
   ruta observada. La clave de lockout, la clasificación de endpoints y la
   lista de rutas públicas deben usar ``scope["path"]``.
2. El bucket de rate-limit incluía ``sha256(X-API-Key)``: una cabecera del
   cliente sin validar, así que un valor aleatorio por petición creaba un
   bucket nuevo y anulaba el límite.
"""

from unittest.mock import AsyncMock

import pytest
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.core import rate_limit as rl


def make_request(path: str, peer: str = "203.0.113.50", headers: dict | None = None) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": path,
            "raw_path": path.encode(),
            "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
            "scheme": "https",
            "query_string": b"",
            "server": ("api.sesis.local", 443),
            "client": (peer, 12345),
        }
    )


class TestRequestPathBinding:
    def test_host_header_with_path_cannot_change_routing_path(self):
        request = make_request(
            "/api/v1/auth/login", headers={"Host": "api.sesis.local/x"}
        )
        assert rl.request_path(request) == "/api/v1/auth/login"

    def test_host_header_does_not_change_public_path_detection(self):
        from app.core.auth_middleware import PUBLIC_PATHS

        request = make_request(
            "/api/v1/c2/assets", headers={"Host": "api.sesis.local/api/v1/auth/login"}
        )
        assert rl.request_path(request) not in PUBLIC_PATHS

    def test_empty_scope_path_falls_back_to_root(self):
        request = make_request("")
        assert rl.request_path(request) == "/"


class _RecordingLimiter:
    def __init__(self):
        self.keys = []

    async def is_allowed(self, key, max_requests, window):
        self.keys.append(key)
        return True, {
            "allowed": True,
            "limit": max_requests,
            "remaining": 1,
            "retry_after": 0,
        }


@pytest.mark.asyncio
class TestBruteForceFailMode:
    """SEC-FIX-001: sin Redis el lockout debe denegar en closed, no romper."""

    async def _is_locked(self, mode: str, env: str) -> bool:
        from unittest.mock import patch

        from app.api.osint.auth import BruteForceProtector
        from app.core.config import settings

        monkeypatch_pairs = {"SECURITY_FAIL_MODE": mode, "ENVIRONMENT": env}
        originals = {k: getattr(settings, k) for k in monkeypatch_pairs}
        try:
            for key, value in monkeypatch_pairs.items():
                object.__setattr__(settings, key, value)
            with patch(
                "app.db.redis_pool.get_redis_pool",
                side_effect=RuntimeError("redis down"),
            ):
                return await BruteForceProtector.is_locked(
                    "audit-probe", "/api/v1/auth/login"
                )
        finally:
            for key, value in originals.items():
                object.__setattr__(settings, key, value)

    async def test_closed_mode_denies_when_redis_is_down(self):
        assert await self._is_locked("closed", "production") is True

    async def test_open_mode_allows_when_redis_is_down(self):
        assert await self._is_locked("open", "development") is False


@pytest.mark.asyncio
class TestRateLimitIdentity:
    async def _dispatch(self, headers: dict, path: str = "/api/v1/auth/login"):
        middleware = rl.RateLimitMiddleware(
            app=AsyncMock(), redis_client=None, fail_closed=False
        )
        recorder = _RecordingLimiter()
        middleware.limiter = recorder
        request = make_request(path, headers=headers)
        request.state.principal = None
        request.state.clearance = "OPEN"
        await middleware.dispatch(
            request, AsyncMock(return_value=JSONResponse({"ok": True}))
        )
        return recorder

    async def test_random_api_key_does_not_create_new_bucket(self):
        keys = []
        for i in range(3):
            recorder = await self._dispatch({"X-API-Key": f"attacker-controlled-{i}"})
            keys.extend(recorder.keys)
        assert len(set(keys)) == 1, keys

    async def test_login_bucket_is_still_classified_as_login(self):
        recorder = await self._dispatch({})
        assert all(key.startswith("login:") for key in recorder.keys)

    async def test_authenticated_subject_keeps_its_own_bucket(self):
        middleware = rl.RateLimitMiddleware(
            app=AsyncMock(), redis_client=None, fail_closed=False
        )
        recorder = _RecordingLimiter()
        middleware.limiter = recorder
        request = make_request("/api/v1/c2/assets")
        request.state.principal = {"sub": "operator-7"}
        request.state.clearance = "OPEN"
        await middleware.dispatch(
            request, AsyncMock(return_value=JSONResponse({"ok": True}))
        )
        assert any(key.endswith("sub:operator-7") for key in recorder.keys)
