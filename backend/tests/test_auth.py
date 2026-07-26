import pytest
from httpx import AsyncClient


class TestAuth:
    async def test_login_correct_creds(self, async_client: AsyncClient, db_session):
        from app.core.security import hash_password
        from app.db.models.persistence import User
        import uuid
        user = User(
            id=str(uuid.uuid4()),
            username="loginuser",
            email="login@sesis.mil",
            hashed_password=hash_password("correctpass"),
            role="operator",
            classification_level="RESTRICTED",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        response = await async_client.post("/api/v1/auth/login", json={
            "username": "loginuser",
            "password": "correctpass",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_incorrect_creds(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass",
        })
        assert response.status_code == 401

    async def test_register(self, async_client: AsyncClient):
        response = await async_client.post("/api/v1/auth/register", json={
            "username": "newoperator",
            "password": "securepass123",
            "email": "new@sesis.mil",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newoperator"
        assert data["is_active"] is False
        assert data["role"] == "operator"

    async def test_health(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_alerts_without_token(self, async_client: AsyncClient):
        response = await async_client.get("/api/v1/c2/")
        assert response.status_code == 401

    async def test_logout_valid_token(self, async_client: AsyncClient, auth_headers):
        response = await async_client.post("/api/v1/auth/logout", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "Sesion cerrada" in data["detail"]

    async def test_refresh_rotation_after_logout(self, async_client: AsyncClient, auth_headers, test_user):
        from app.core.security import create_refresh_token
        token_data = {
            "sub": test_user.id,
            "username": test_user.username,
            "role": test_user.role,
            "clearance": test_user.classification_level,
        }
        refresh_token = create_refresh_token(token_data)

        response = await async_client.post(
            "/api/v1/auth/logout",
            headers=auth_headers,
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200

        response = await async_client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert response.status_code == 401
