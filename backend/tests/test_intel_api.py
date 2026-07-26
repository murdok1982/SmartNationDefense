import pytest


class TestIntelAPI:
    async def test_intel_status_with_token(self, async_client, auth_headers):
        response = await async_client.get("/api/v1/intel/status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "module" in data
        assert "status" in data

    async def test_intel_reports_with_token(self, async_client, auth_headers):
        response = await async_client.get("/api/v1/agents/intel/reports", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "reports" in data
        assert isinstance(data["reports"], list)

    async def test_intel_returns_json_not_string(self, async_client, auth_headers):
        response = await async_client.get("/api/v1/intel/status", headers=auth_headers)
        data = response.json()
        assert isinstance(data, dict)
        assert not isinstance(data, str)
