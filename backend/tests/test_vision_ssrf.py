"""SEC-FIX-002 — regresion SSRF en descarga de imagenes (vision/Maven).

Antes del fix, ``SatelliteAnalyst._download_image`` hacia
``httpx.AsyncClient(follow_redirects=True).get(url)`` sin validacion,
permitiendo SSRF a metadatos cloud y servicios internos desde
``/api/v3/vision/*``.

Estos tests fijan el comportamiento seguro: toda URL interna debe ser
rechazada antes de cualquier conexion de red.
"""
import pytest

from app.services.vision.analyst import SatelliteAnalyst


BLOCKED_URLS = [
    "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://127.0.0.1:8000/api/v1/health",
    "http://10.0.0.5/internal",
    "http://192.168.1.1/",
    "http://[::1]/",
    "http://localhost/",
    "file:///etc/passwd",
    "gopher://127.0.0.1:6379/_INFO",
]


class TestVisionDownloadSSRF:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("url", BLOCKED_URLS)
    async def test_internal_urls_are_rejected(self, url: str):
        analyst = SatelliteAnalyst()
        with pytest.raises(ValueError):
            await analyst._download_image(url)

    @pytest.mark.asyncio
    async def test_private_ipv4_mapped_ipv6_is_rejected(self):
        analyst = SatelliteAnalyst()
        with pytest.raises(ValueError):
            await analyst._download_image("http://[::ffff:169.254.169.254]/")
