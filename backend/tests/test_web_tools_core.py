# -*- coding: utf-8 -*-
"""Cobertura de web_tools: SSRF, redirects, peer pinning y tools (AC-22)."""

import importlib
import sys
import types
from unittest.mock import AsyncMock, patch

import pytest

web_tools = importlib.import_module("app.services.osint.tools.web_tools")
WebFetchTool = web_tools.WebFetchTool
WebSearchTool = web_tools.WebSearchTool
IpGeolocationTool = web_tools.IpGeolocationTool


class FakeResponse:
    def __init__(
        self,
        *,
        status_code=200,
        headers=None,
        text="",
        url="https://example.com/",
        is_redirect=False,
        extensions=None,
        json_data=None,
    ):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text
        self.url = url
        self.is_redirect = is_redirect
        self.extensions = extensions or {}
        self._json = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


class FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def get(self, url, headers=None, follow_redirects=False):
        self.calls.append(url)
        return self._responses.pop(0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


@pytest.mark.asyncio
class TestSafeHttpGet:
    async def test_success_returns_response(self):
        resp = FakeResponse(text="ok")
        client = FakeClient([resp])
        with patch.object(web_tools, "is_safe_url_async", AsyncMock(return_value=True)), \
             patch.object(web_tools, "_resolve_validated_ips", AsyncMock(return_value=["93.184.216.34"])):
            result = await web_tools.safe_http_get(client, "https://example.com/")
        assert result is resp

    async def test_blocked_url_raises(self):
        with patch.object(web_tools, "is_safe_url_async", AsyncMock(return_value=False)):
            with pytest.raises(ValueError, match="SSRF protection"):
                await web_tools.safe_http_get(FakeClient([]), "http://127.0.0.1/")

    async def test_follows_redirect_until_final(self):
        redirect = FakeResponse(
            status_code=302,
            headers={"location": "/next"},
            is_redirect=True,
        )
        final = FakeResponse(text="final")
        client = FakeClient([redirect, final])
        with patch.object(web_tools, "is_safe_url_async", AsyncMock(return_value=True)), \
             patch.object(web_tools, "_resolve_validated_ips", AsyncMock(return_value=["93.184.216.34"])):
            result = await web_tools.safe_http_get(client, "https://example.com/start")
        assert result is final
        assert client.calls == ["https://example.com/start", "https://example.com/next"]

    async def test_redirect_without_location_returns_response(self):
        redirect = FakeResponse(status_code=302, is_redirect=True, headers={})
        with patch.object(web_tools, "is_safe_url_async", AsyncMock(return_value=True)), \
             patch.object(web_tools, "_resolve_validated_ips", AsyncMock(return_value=["93.184.216.34"])):
            result = await web_tools.safe_http_get(FakeClient([redirect]), "https://example.com/")
        assert result is redirect

    async def test_too_many_redirects_raises(self):
        redirects = [FakeResponse(status_code=302, headers={"location": "/loop"}, is_redirect=True) for _ in range(5)]
        with patch.object(web_tools, "is_safe_url_async", AsyncMock(return_value=True)), \
             patch.object(web_tools, "_resolve_validated_ips", AsyncMock(return_value=["93.184.216.34"])):
            with pytest.raises(ValueError, match="Too many redirects"):
                await web_tools.safe_http_get(FakeClient(redirects), "https://example.com/", max_redirects=2)

    async def test_peer_address_mismatch_raises(self):
        class Stream:
            def get_extra_info(self, name):
                return ("10.0.0.9", 443)

        resp = FakeResponse(extensions={"network_stream": Stream()})
        with patch.object(web_tools, "is_safe_url_async", AsyncMock(return_value=True)), \
             patch.object(web_tools, "_resolve_validated_ips", AsyncMock(return_value=["93.184.216.34"])):
            with pytest.raises(ValueError, match="peer address mismatch"):
                await web_tools.safe_http_get(FakeClient([resp]), "https://example.com/")


@pytest.mark.asyncio
class TestWebFetchTool:
    async def test_blocked_url_returns_error_without_fetch(self):
        result = await WebFetchTool().execute("http://169.254.169.254/latest/meta-data/")
        assert result.success is False
        assert "SSRF" in (result.error or "")

    async def test_extracts_text_title_and_links(self):
        html = "<html><head><title>Tactical</title></head><body><a href='/x'>x</a>Hola</body></html>"
        resp = FakeResponse(headers={"content-type": "text/html"}, text=html, url="https://example.com/")
        with patch.object(web_tools, "safe_http_get", AsyncMock(return_value=resp)):
            result = await WebFetchTool().execute("https://example.com/")
        assert result.success is True
        assert result.data["title"] == "Tactical"
        assert "Hola" in result.data["text"]
        assert result.data["links"] == ["/x"]

    async def test_fetch_exception_returns_error(self):
        with patch.object(web_tools, "safe_http_get", AsyncMock(side_effect=RuntimeError("boom"))):
            result = await WebFetchTool().execute("https://example.com/")
        assert result.success is False
        assert "boom" in (result.error or "")


@pytest.mark.asyncio
class TestWebSearchTool:
    async def test_missing_dependency_returns_error(self):
        result = await WebSearchTool().execute("inteligencia")
        assert result.success is False

    async def test_success_with_fake_ddgs(self):
        class FakeDDGS:
            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def text(self, query, max_results=10):
                return [{"title": "t", "href": "https://example.com", "body": "b"}]

        fake_module = types.SimpleNamespace(DDGS=FakeDDGS)
        with patch.dict(sys.modules, {"duckduckgo_search": fake_module}):
            result = await WebSearchTool().execute("inteligencia")
        assert result.success is True
        assert result.data["results"][0]["title"] == "t"


@pytest.mark.asyncio
class TestIpGeolocationTool:
    async def test_private_ip_rejected(self):
        result = await IpGeolocationTool().execute("10.0.0.1")
        assert result.success is False
        assert "Private IP" in (result.error or "")

    async def test_invalid_ip_rejected(self):
        result = await IpGeolocationTool().execute("no-es-ip")
        assert result.success is False
        assert "Invalid IP" in (result.error or "")

    async def test_success_with_mocked_client(self):
        resp = FakeResponse(json_data={"status": "success", "country": "ES"})
        client = FakeClient([resp])
        with patch.object(web_tools.httpx, "AsyncClient", return_value=client):
            result = await IpGeolocationTool().execute("8.8.8.8")
        assert result.success is True
        assert result.data["country"] == "ES"

    async def test_api_failure_returns_error(self):
        resp = FakeResponse(json_data={"status": "fail", "message": "quota"})
        client = FakeClient([resp])
        with patch.object(web_tools.httpx, "AsyncClient", return_value=client):
            result = await IpGeolocationTool().execute("8.8.8.8")
        assert result.success is False
        assert result.error == "quota"
