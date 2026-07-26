import pytest


class TestRateLimit:
    async def test_login_rate_limit_exceeded(self, async_client):
        for i in range(6):
            response = await async_client.post("/api/v1/auth/login", json={
                "username": f"ratelimit{i}",
                "password": "doesnotmatter",
            })
        assert response.status_code == 429

    async def test_health_always_ok(self, async_client):
        for _ in range(10):
            response = await async_client.get("/api/v1/health")
            assert response.status_code == 200
