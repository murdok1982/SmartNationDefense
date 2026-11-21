# -*- coding: utf-8 -*-
"""Regresión SEC-FIX-005: el login real debe tener lockout por cuenta."""

import uuid

import pytest

from app.api.osint.auth import BruteForceProtector
from app.core.security import hash_password


@pytest.mark.asyncio
class TestRealLoginLockout:
    async def test_locked_account_gets_429_with_retry_after(
        self, async_client, db_session
    ):
        from app.db.models.persistence import User

        username = f"lockout-{uuid.uuid4().hex[:8]}"
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=f"{username}@sesis.mil",
            hashed_password=hash_password("Correct-Pass-123!"),
            role="operator",
            classification_level="RESTRICTED",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        path = "/api/v1/auth/login"
        for _ in range(BruteForceProtector.MAX_ATTEMPTS):
            await BruteForceProtector.record_failure(username, "203.0.113.9", path)

        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "Correct-Pass-123!"},
        )

        assert response.status_code == 429
        assert response.headers.get("Retry-After") == "60"
        assert "bloqueada" in response.json()["detail"].lower()

    async def test_failed_login_records_attempt_and_audit(
        self, async_client, db_session
    ):
        from sqlalchemy import select

        from app.db.models.persistence import AuditLog

        username = f"badlogin-{uuid.uuid4().hex[:8]}"
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "wrong"},
        )
        assert response.status_code == 401

        attempts = await BruteForceProtector.get_remaining_attempts(
            username, "/api/v1/auth/login"
        )
        assert attempts == BruteForceProtector.MAX_ATTEMPTS - 1

        rows = (
            await db_session.execute(
                select(AuditLog).where(AuditLog.resource_id == username)
            )
        ).scalars().all()
        assert any(row.action == "LOGIN" and row.success is False for row in rows)
