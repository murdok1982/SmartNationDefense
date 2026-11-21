# -*- coding: utf-8 -*-
"""Regresión SEC-FIX-001/004: fail-closed y resolución de IP tras proxy."""

from unittest.mock import AsyncMock

import pytest
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.core import rate_limit as rl


def make_request(peer: str, headers: dict | None = None) -> Request:
    raw_headers = [
        (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
    ]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/health",
        "headers": raw_headers,
        "client": (peer, 12345),
        "scheme": "http",
        "server": ("testserver", 80),
        "query_string": b"",
    }
    return Request(scope)


class TestResolveClientIp:
    def test_untrusted_peer_cannot_spoof_x_real_ip(self):
        request = make_request("198.51.100.7", {"X-Real-IP": "1.2.3.4"})
        assert rl.resolve_client_ip(request) == "198.51.100.7"

    def test_trusted_proxy_uses_x_real_ip(self):
        request = make_request("127.0.0.1", {"X-Real-IP": "203.0.113.5"})
        assert rl.resolve_client_ip(request) == "203.0.113.5"

    def test_trusted_proxy_uses_first_forwarded_for(self):
        request = make_request(
            "172.18.0.5", {"X-Forwarded-For": "203.0.113.6, 10.0.0.1"}
        )
        assert rl.resolve_client_ip(request) == "203.0.113.6"

    def test_invalid_forwarded_header_falls_back_to_peer(self):
        request = make_request("127.0.0.1", {"X-Real-IP": "not-an-ip"})
        assert rl.resolve_client_ip(request) == "127.0.0.1"


class _BrokenLimiter:
    async def is_allowed(self, *args, **kwargs):
        raise RuntimeError("redis down")


@pytest.mark.asyncio
class TestRateLimitFailMode:
    async def _dispatch(self, fail_closed: bool):
        middleware = rl.RateLimitMiddleware(
            app=AsyncMock(), redis_client=None, fail_closed=fail_closed
        )
        middleware.limiter = _BrokenLimiter()
        request = make_request("127.0.0.1")
        request.state.principal = None
        request.state.clearance = "OPEN"
        call_next = AsyncMock(return_value=JSONResponse({"ok": True}))
        return await middleware.dispatch(request, call_next), call_next

    async def test_fail_closed_returns_503_without_calling_next(self):
        response, call_next = await self._dispatch(fail_closed=True)
        assert response.status_code == 503
        assert response.headers.get("Retry-After") == "30"
        call_next.assert_not_called()

    async def test_fail_open_in_dev_calls_next(self):
        response, call_next = await self._dispatch(fail_closed=False)
        assert response.status_code == 200
        call_next.assert_awaited_once()

    async def test_authenticated_subject_has_own_bucket(self):
        class RecordingLimiter:
            def __init__(self):
                self.keys = []

            async def is_allowed(self, key, max_requests, window):
                self.keys.append(key)
                return True, {"allowed": True, "limit": max_requests, "remaining": 1, "retry_after": 0}

        middleware = rl.RateLimitMiddleware(
            app=AsyncMock(), redis_client=None, fail_closed=False
        )
        recorder = RecordingLimiter()
        middleware.limiter = recorder
        request = make_request("203.0.113.9")
        request.state.principal = {"sub": "operator-42"}
        request.state.clearance = "OPEN"

        response = await middleware.dispatch(
            request, AsyncMock(return_value=JSONResponse({"ok": True}))
        )
        assert response.status_code == 200
        assert any("sub:operator-42" in key for key in recorder.keys)
