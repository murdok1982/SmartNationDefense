from __future__ import annotations

import time
from types import SimpleNamespace
from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import *
from app.db.session import get_db
from app.db.models.osint.user import User

bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Token blacklist — in-memory fallback if Redis is unavailable
# ---------------------------------------------------------------------------


class _TokenBlacklist:
    def __init__(self):
        self._redis = None
        self._mem: dict[str, float] = {}

    async def is_blacklisted(self, jti: str) -> bool:
        if not jti:
            return False
        if self._redis is not None:
            try:
                return bool(await self._redis.exists(f"revoked:{jti}"))
            except Exception:
                pass
        return jti in self._mem

    async def is_user_revoked(self, sub: str) -> bool:
        key = f"user_revoked:{sub}"
        if self._redis is not None:
            try:
                return bool(await self._redis.exists(key))
            except Exception:
                pass
        return key in self._mem

    async def add(self, jti: str, exp: float) -> None:
        ttl = max(1, int(exp - time.time()))
        if self._redis is not None:
            try:
                await self._redis.setex(f"revoked:{jti}", ttl, "1")
                return
            except Exception:
                pass
        self._mem[jti] = exp

    async def revoke_all_user_tokens(self, user_id: str, exp: float) -> None:
        key = f"user_revoked:{user_id}"
        ttl = max(1, int(exp - time.time()))
        if self._redis is not None:
            try:
                await self._redis.setex(key, ttl, "1")
                return
            except Exception:
                pass
        self._mem[key] = exp


token_blacklist = _TokenBlacklist()


async def get_redis() -> aioredis.Redis | None:
    try:
        from app.db.redis_pool import get_redis_pool
        return await get_redis_pool()
    except Exception:
        return None


async def get_token_blacklist() -> _TokenBlacklist:
    if token_blacklist._redis is None:
        redis_client = await get_redis()
        if redis_client is not None:
            token_blacklist._redis = redis_client
    return token_blacklist


def verify_token(token: str) -> SimpleNamespace:
    try:
        payload = decode_token(token)
        return SimpleNamespace(**payload)
    except HTTPException:
        raise ValueError("Invalid token")


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = verify_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.type != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    blacklist = await get_token_blacklist()
    if await blacklist.is_blacklisted(payload.jti):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    if await blacklist.is_user_revoked(payload.sub):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="All sessions revoked")

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    return user

async def get_current_active_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user

def require_scope(scope: str):
    async def _check(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if "admin" not in user.scopes and scope not in user.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{scope}' required",
            )
        return user

    return _check

_CLEARANCE_ORDER = ["UNCLASSIFIED", "CUI", "RESTRICTED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]

def _clearance_index(level: str | None) -> int:
    if not level:
        return 0
    try:
        return _CLEARANCE_ORDER.index(level)
    except ValueError:
        return 0

def user_can_access_classification(user: User, resource_classification: str | None) -> bool:
    """True iff the user's clearance is greater-or-equal to the resource's level."""
    if getattr(user, "is_superuser", False):
        return True
    return _clearance_index(getattr(user, "classification", "UNCLASSIFIED")) >= _clearance_index(
        resource_classification
    )

def assert_resource_access(
    user: User,
    *,
    owner_id: str | None,
    classification: str | None = "UNCLASSIFIED",
) -> None:
    """Centralized BOLA + clearance gate.

    Raises 403 if either:
      - the user is not the resource owner (and not admin/superuser), or
      - the user's clearance is below the resource's classification.
    Raises 404-style HTTPException is the caller's choice — this helper does not
    leak existence information beyond ``Forbidden``.
    """
    is_admin = getattr(user, "is_superuser", False) or "admin" in (user.scopes or [])
    if not is_admin and owner_id and owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Resource does not belong to caller",
        )
    if not user_can_access_classification(user, classification):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient clearance for resource classification",
        )

def require_classification(min_level: str):
    min_idx = _clearance_index(min_level)

    async def _check(user: Annotated[User, Depends(get_current_active_user)]) -> User:
        if _clearance_index(getattr(user, "classification", "UNCLASSIFIED")) < min_idx:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Classification '{min_level}' or higher required",
            )
        return user

    return _check

async def require_admin(user: Annotated[User, Depends(get_current_active_user)]) -> User:
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user

async def require_tenant_access(user: Annotated[User, Depends(get_current_active_user)], tenant_id: str = "") -> User:
    if settings.MULTI_TENANT:
        user_tenant = getattr(user, "tenant_id", settings.DEFAULT_TENANT_ID)
        if user_tenant != tenant_id and "admin" not in user.scopes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant access denied")
    return user

DBSession = Annotated[AsyncSession, Depends(get_db)]
RedisConn = Annotated[aioredis.Redis, Depends(get_redis)]
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(require_admin)]
