import importlib
import inspect
import pytest
from unittest.mock import patch, AsyncMock
from pathlib import Path

web_tools = importlib.import_module("app.services.osint.tools.web_tools")
_is_safe_url = web_tools._is_safe_url
is_safe_url_async = web_tools.is_safe_url_async
safe_http_get = web_tools.safe_http_get

document_tools = importlib.import_module("app.services.osint.tools.document_tools")
DocumentExtractTool = document_tools.DocumentExtractTool


class TestSSRF:
    def test_rejects_private_ip_127(self):
        assert _is_safe_url("http://127.0.0.1/") is False
        assert _is_safe_url("http://127.0.0.1:8080/admin") is False

    def test_rejects_private_ip_10(self):
        assert _is_safe_url("http://10.0.0.1/") is False
        assert _is_safe_url("http://10.1.2.3:8000/") is False

    def test_rejects_private_ip_192_168(self):
        assert _is_safe_url("http://192.168.1.1/") is False

    def test_accepts_public_ip(self):
        assert _is_safe_url("http://93.184.216.34/") is True
        assert _is_safe_url("https://8.8.8.8/") is True

    def test_rejects_private_hostname(self):
        assert _is_safe_url("http://localhost/") is False
        assert _is_safe_url("http://localhost.localdomain/") is False

    def test_rejects_metadata_hostname(self):
        assert _is_safe_url("http://169.254.169.254/") is False
        assert _is_safe_url("http://metadata.google.internal/") is False

    async def test_dns_rebinding_block(self):
        with patch("asyncio.get_running_loop") as mock_loop:
            fake_gai = AsyncMock(return_value=[
                (0, 0, 0, "", ("127.0.0.1", 0)),
            ])
            mock_loop.return_value.getaddrinfo = fake_gai
            result = await is_safe_url_async("http://evil.malicious.com/")
            assert result is False

    async def test_redirect_to_private_ip_blocked(self):
        import httpx

        mock_resp = httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})
        transport = httpx.MockTransport(lambda req: mock_resp)

        async with httpx.AsyncClient(transport=transport) as client:
            with patch.object(web_tools, "is_safe_url_async") as mock_is_safe:
                mock_is_safe.side_effect = [True, False]
                with pytest.raises(ValueError, match="URL blocked"):
                    await safe_http_get(client, "http://example.com/")

    async def test_document_path_outside_allowed_dir(self):
        import tempfile
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            allowed = Path(tmpdir) / "allowed"
            allowed.mkdir()
            forbidden_file = Path(tmpdir) / "secret.txt"
            forbidden_file.write_text("secreto")

            tool = DocumentExtractTool(config=None)
            with patch.object(tool, "_rate_limit_check", return_value=None):
                with patch("app.core.config.settings.OSINT_DOCS_ALLOWED_DIR", str(allowed)):
                    result = await tool.execute(file_path=str(forbidden_file))
                    assert result.success is False
                    assert "fuera del directorio" in result.error
