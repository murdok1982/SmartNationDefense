import pytest
from unittest.mock import patch

from app.services.terrain.elevation import ElevationProviderError


class TestTerrain:
    async def test_elevation_success(self, async_client, auth_headers):
        with patch("app.services.terrain.service.fetch_elevations") as mock_fetch:
            mock_fetch.return_value = [123.4]
            response = await async_client.get(
                "/api/v1/terrain/elevation?lat=40.4168&lon=-3.7038",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, dict)
            assert "elevation_m" in data
            assert data["elevation_m"] == 123.4

    async def test_elevation_provider_failure(self, async_client, auth_headers):
        with patch("app.services.terrain.service.fetch_elevations") as mock_fetch:
            mock_fetch.side_effect = ElevationProviderError("DEM timeout")
            response = await async_client.get(
                "/api/v1/terrain/elevation?lat=40.4168&lon=-3.7038",
                headers=auth_headers,
            )
            assert response.status_code == 503
            data = response.json()
            assert "detail" in data
