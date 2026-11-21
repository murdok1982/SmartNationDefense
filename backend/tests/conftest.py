import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!!!")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:63799/0")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")
os.environ.setdefault("ADMIN_INITIAL_PASSWORD", "test-admin-pass-007")
os.environ.setdefault("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

test_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
test_async_session = async_sessionmaker(test_engine, expire_on_commit=False)

import app.db.session as db_session_module
db_session_module.engine = test_engine
db_session_module.async_session = test_async_session
db_session_module.async_session_factory = test_async_session

from app.core.config import settings
from app.db.models.persistence import Base, User
from app.core.security import hash_password, create_access_token, create_refresh_token
from app.db.session import get_db


class FakeRedis:
    def __init__(self):
        self._data: dict = {}
        self._zsets: dict = {}

    async def ping(self) -> bool:
        return True

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._data[key] = value

    async def exists(self, key: str) -> int:
        return 1 if key in self._data else 0

    async def get(self, key: str):
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool | None:
        if nx and key in self._data:
            return None
        self._data[key] = value
        return True

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)
        # Redis borra la clave sea cual sea su tipo: si no se limpian los
        # ZSET, record_success() dejaría intentos fantasma (test-double falso).
        self._zsets.pop(key, None)

    async def zremrangebyscore(self, key: str, min_val, max_val) -> None:
        if key in self._zsets:
            min_v = float(min_val) if min_val != "-inf" else float("-inf")
            max_v = float(max_val) if max_val != "+inf" else float("+inf")
            self._zsets[key] = {
                m: s for m, s in self._zsets[key].items()
                if not (min_v < s < max_v)
            }

    async def zcard(self, key: str) -> int:
        return len(self._zsets.get(key, {}))

    async def zadd(self, key: str, mapping: dict) -> None:
        if key not in self._zsets:
            self._zsets[key] = {}
        self._zsets[key].update(mapping)

    async def zrange(self, key: str, start: int, stop: int, withscores: bool = False):
        if key not in self._zsets:
            return []
        sorted_items = sorted(self._zsets[key].items(), key=lambda x: x[1])
        items = sorted_items[start:stop + 1] if stop >= 0 else sorted_items[start:]
        if withscores:
            return [(m, s) for m, s in items]
        return [m for m, s in items]

    async def expire(self, key: str, ttl: int) -> None:
        pass

    def __await__(self):
        return self.ping().__await__()


fake_redis = FakeRedis()

import app.db.redis_pool

async def _fake_get_redis_pool():
    return fake_redis

app.db.redis_pool.get_redis_pool = _fake_get_redis_pool
app.db.redis_pool.get_redis_client = lambda: fake_redis


@pytest.fixture(autouse=True)
async def _setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _reset_fake_redis():
    """Aísla el estado Redis entre tests (rate-limit/lockout/circuit breaker).

    Sin esto, un test podía heredar contadores de otro y el orden de ejecución
    alteraba el resultado (falso verde/rojo).
    """
    fake_redis._data.clear()
    fake_redis._zsets.clear()
    yield


@pytest.fixture
async def db_session(_setup_database) -> AsyncGenerator[AsyncSession, None]:
    async with test_async_session() as session:
        yield session


@asynccontextmanager
async def noop_lifespan(app):
    yield


from fastapi import Depends


@pytest.fixture(scope="session")
def raw_app():
    from fastapi import FastAPI
    from app.core.rate_limit import RateLimitMiddleware
    from app.core.auth_middleware import AuthMiddleware

    app = FastAPI(lifespan=noop_lifespan)
    app.add_middleware(RateLimitMiddleware, redis_client=fake_redis)
    app.add_middleware(AuthMiddleware)

    from app.api.health import router as health_router
    app.include_router(health_router, prefix="/api/v1", tags=["Health"])

    from app.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])

    from app.api.v1 import alerts
    from app.core.security import get_current_user
    _AUTH_DEPS = [Depends(get_current_user)]
    app.include_router(alerts.router, prefix="/api/v1/c2", tags=["C2"], dependencies=_AUTH_DEPS)

    from app.api.agents import intel_api
    app.include_router(intel_api.router, prefix="/api/v1/agents/intel", tags=["Agents"], dependencies=_AUTH_DEPS)

    from app.api.intel.router import router as intel_router
    app.include_router(intel_router, prefix="/api/v1/intel", tags=["Intelligence"], dependencies=_AUTH_DEPS)

    from app.api.v1 import terrain
    app.include_router(terrain.router, prefix="/api/v1/terrain", tags=["Terrain"], dependencies=_AUTH_DEPS)

    return app


async def _get_test_db():
    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
async def async_client(raw_app, _setup_database):
    raw_app.dependency_overrides[get_db] = _get_test_db

    try:
        from httpx import ASGITransport
        transport = ASGITransport(app=raw_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    except ImportError:
        async with AsyncClient(app=raw_app, base_url="http://test") as client:
            yield client

    raw_app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session) -> User:
    user = User(
        id=str(uuid.uuid4()),
        username="testuser",
        email="test@sesis.mil",
        hashed_password=hash_password("testpass123"),
        role="operator",
        classification_level="RESTRICTED",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_headers(test_user) -> dict:
    token_data = {
        "sub": test_user.id,
        "username": test_user.username,
        "role": test_user.role,
        "clearance": test_user.classification_level,
    }
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def anyio_backend():
    return "asyncio"
