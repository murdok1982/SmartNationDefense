import uuid

import pytest

from app.api.osint.auth import BruteForceProtector, _BruteForceProtector


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


LOGIN = "/api/v1/auth/login"
MFA = "/api/v1/auth/mfa/verify"


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


@pytest.mark.asyncio
class TestDistributedBruteForce:
    """SEC-TEST-BRUTE-01: el estado vive en Redis (no en memoria del proceso).

    FakeRedis de conftest actúa como backend compartido: un segundo protector
    (otro worker) debe ver el lockout creado por el primero.
    """

    async def test_lockout_after_max_attempts(self):
        user = _unique("bf")
        for _ in range(BruteForceProtector.MAX_ATTEMPTS):
            await BruteForceProtector.record_failure(user, "127.0.0.1", LOGIN)

        assert await BruteForceProtector.is_locked(user, LOGIN) is True
        assert await BruteForceProtector.get_remaining_attempts(user, LOGIN) == 0

    async def test_lockout_is_path_scoped(self):
        user = _unique("bfp")
        for _ in range(BruteForceProtector.MAX_ATTEMPTS):
            await BruteForceProtector.record_failure(user, "127.0.0.1", LOGIN)

        assert await BruteForceProtector.is_locked(user, LOGIN) is True
        # El mismo usuario en otro endpoint no hereda el lockout (N-06).
        assert await BruteForceProtector.is_locked(user, MFA) is False

    async def test_lockout_visible_to_second_worker(self):
        user = _unique("bfd")
        for _ in range(BruteForceProtector.MAX_ATTEMPTS):
            await BruteForceProtector.record_failure(user, "127.0.0.1", LOGIN)

        other_worker = _BruteForceProtector()
        assert await other_worker.is_locked(user, LOGIN) is True

    async def test_success_resets_counter_and_lock(self):
        user = _unique("bfr")
        for _ in range(3):
            await BruteForceProtector.record_failure(user, "127.0.0.1", LOGIN)

        await BruteForceProtector.record_success(user, "127.0.0.1", LOGIN)

        assert await BruteForceProtector.is_locked(user, LOGIN) is False
        assert (
            await BruteForceProtector.get_remaining_attempts(user, LOGIN)
            == BruteForceProtector.MAX_ATTEMPTS
        )
