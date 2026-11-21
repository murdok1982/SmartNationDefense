from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.osint.deps import (
    DBSession,
    CurrentUser,
    AdminUser,
    get_db,
    get_current_active_user,
    require_admin,
    get_token_blacklist,
)
from app.core.audit import audit_chain
from app.core.config import settings
from app.core.events import event_bus
from app.core.rate_limit import CircuitBreaker, get_limiter_key, request_path

logger = logging.getLogger(__name__)
from app.core.security import (
    create_access_token,
    create_mfa_challenge_token,
    create_refresh_token,
    decode_mfa_token,
    decode_token,
    hash_password,
    is_jti_revoked,
    revoke_jti,
    verify_password,
)
from app.services.intel.auth.mfa import totp_service
from app.db.models.osint.user import User

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class MfaVerifyRequest(BaseModel):
    mfa_ticket: str
    code: str = Field(..., min_length=6, max_length=8)


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class MfaEnableRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=8)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 900


class LoginResponse(BaseModel):
    mfa_required: bool = False
    mfa_ticket: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None


class TokenRefresh(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., max_length=256)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = ""
    classification: str = "UNCLASSIFIED"
    tenant_id: str = "default"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str = ""
    is_active: bool = True
    is_superuser: bool = False
    scopes: list[str] = []
    classification: str = "UNCLASSIFIED"
    tenant_id: str = "default"

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Brute-force protection (Redis ZSET sliding window, distribuido)
# ---------------------------------------------------------------------------


class _BruteForceProtector:
    def __init__(self):
        self.MAX_ATTEMPTS = 5
        self.WINDOW = 300
        self.circuit = CircuitBreaker()

    async def is_locked(self, username: str, path: str = "") -> bool:
        key = get_limiter_key(username, path)
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            if r is not None:
                self.circuit.redis = r
                # TASK-013: circuit breaker — deniega mientras el circuito
                # está OPEN (fail-open: se permite si Redis no está disponible).
                if not await asyncio.to_thread(
                    self.circuit.check, key, self.MAX_ATTEMPTS, self.WINDOW, self.MAX_ATTEMPTS
                ):
                    return True
            if await r.exists(f"lockout:{key}"):
                return True
            if await r.zcard(f"bf_attempts:{key}") >= self.MAX_ATTEMPTS:
                await r.setex(f"lockout:{key}", self.WINDOW * 2, "1")
                return True
        except Exception as exc:
            # SEC-FIX-001: sin Redis no se puede demostrar que la cuenta no
            # está bloqueada; en modo closed se deniega (el arranque ya habría
            # abortado, pero cubre caídas posteriores).
            if settings.security_fail_closed:
                logger.error("BruteForce: Redis no disponible en modo closed: %s", exc)
                return True
        return False

    async def get_remaining_attempts(self, username: str, path: str = "") -> int:
        key = get_limiter_key(username, path)
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            cnt = await r.zcard(f"bf_attempts:{key}")
            return max(0, self.MAX_ATTEMPTS - cnt)
        except Exception:
            return self.MAX_ATTEMPTS

    async def record_failure(self, username: str, ip: str, path: str = "") -> None:
        key = get_limiter_key(username, path)
        r = None
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            if r is not None:
                self.circuit.redis = r
            now = datetime.now(timezone.utc).timestamp()
            member = str(time.time_ns())
            attempts_key = f"bf_attempts:{key}"
            await r.zadd(attempts_key, {member: now})
            await r.zremrangebyscore(attempts_key, "-inf", now - self.WINDOW)
            cnt = await r.zcard(attempts_key)
            if cnt >= self.MAX_ATTEMPTS:
                await r.setex(f"lockout:{key}", self.WINDOW * 2, "1")
        except Exception:
            pass
        if r is not None:
            try:
                await asyncio.to_thread(
                    self.circuit.report_failure, key, self.MAX_ATTEMPTS
                )
            except Exception:
                pass

    async def record_success(self, username: str, ip: str, path: str = "") -> None:
        key = get_limiter_key(username, path)
        r = None
        try:
            from app.db.redis_pool import get_redis_pool
            r = await get_redis_pool()
            if r is not None:
                self.circuit.redis = r
                await r.delete(f"bf_attempts:{key}")
                await r.delete(f"lockout:{key}")
        except Exception:
            pass
        if r is not None:
            try:
                await asyncio.to_thread(self.circuit.report_success, key)
            except Exception:
                pass


BruteForceProtector = _BruteForceProtector()


# ---------------------------------------------------------------------------
# MFA helpers (AES-256-GCM encrypted at rest & isolated challenge tokens)
# ---------------------------------------------------------------------------


def _issue_mfa_ticket(user_id: str, **kw: object) -> str:
    return create_mfa_challenge_token(user_id)


async def is_mfa_ticket_used(jti: str | None) -> bool:
    if not jti:
        return False
    try:
        from app.db.redis_pool import get_redis_pool
        r = await get_redis_pool()
        return bool(await r.exists(f"mfa_ticket_used:{jti}"))
    except Exception:
        return False


async def _mark_mfa_ticket_used(jti: str, exp: int) -> None:
    try:
        from app.db.redis_pool import get_redis_pool
        r = await get_redis_pool()
        ttl = max(1, int(exp) - int(datetime.now(timezone.utc).timestamp()))
        await r.setex(f"mfa_ticket_used:{jti}", ttl, "1")
        await revoke_jti(jti, exp)
    except Exception:
        pass


async def _verify_mfa_ticket(ticket: str) -> dict:
    payload = decode_mfa_token(ticket)
    jti = payload.get("jti")
    if jti:
        try:
            if await is_mfa_ticket_used(jti) or await is_jti_revoked(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="MFA challenge ya consumido o revocado",
                )
            exp = payload.get("exp", 0)
            await _mark_mfa_ticket_used(jti, exp)
        except HTTPException:
            raise
        except Exception:
            pass
    return payload


def _generate_secret() -> str:
    return totp_service.generate_secret()


def _provisioning_uri(secret: str, account: str = "user") -> str:
    return totp_service.provisioning_uri(account, secret)


def _encrypt_secret(secret: str) -> str:
    return totp_service.encrypt_secret(secret)


def _decrypt_secret(secret_or_encrypted: str) -> str:
    try:
        return totp_service.decrypt_secret(secret_or_encrypted)
    except Exception:
        return secret_or_encrypted


def _verify_code(secret_or_encrypted: str, code: str) -> bool:
    plain = _decrypt_secret(secret_or_encrypted)
    return totp_service.verify_code(plain, code)


def _create_token_pair(
    user_id: str,
    scopes: list[str] | None = None,
    classification: str = "UNCLASSIFIED",
    session_id: str | None = None,
) -> SimpleNamespace:
    data: dict[str, object] = {
        "sub": user_id,
        "scopes": scopes or [],
        "clearance": classification,
    }
    if session_id:
        data["sid"] = session_id
    access = create_access_token(data)
    refresh = create_refresh_token(data)
    return SimpleNamespace(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        session_id=session_id or "",
    )


def _validate_password_strength(password: str) -> list[str]:
    issues: list[str] = []
    if len(password) < 8:
        issues.append("Password must be at least 8 characters")
    if not any(c.isupper() for c in password):
        issues.append("Password must contain an uppercase letter")
    if not any(c.isdigit() for c in password):
        issues.append("Password must contain a digit")
    return issues


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------


async def _log_audit(
    user_id: str,
    action: str,
    resource: str,
    resource_id: str,
    ip: str,
    success: bool = True,
    error: str | None = None,
    details: dict | None = None,
    db_session: AsyncSession | None = None,
) -> None:
    """Registra el evento en la cadena de auditoría (hash chain).

    ``db_session`` es opcional: cuando se pasa, la entrada se persiste en la
    tabla canónica ``audit_log`` (TASK-015/TASK-027). Sin sesión, la entrada
    sólo vive en memoria (comportamiento histórico).
    """
    payload: dict = {"ip": ip, "success": success}
    if error:
        payload["error"] = error
    if details:
        payload.update(details)
    await audit_chain.record(
        event=action,
        actor=user_id,
        resource=f"{resource}:{resource_id}",
        details=payload,
        db_session=db_session,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


async def _issue_tokens_for(user: User, request: Request, db: AsyncSession, client_ip: str) -> LoginResponse:
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.now(timezone.utc), last_ip=client_ip)
    )
    await db.commit()

    await BruteForceProtector.record_success(user.username, client_ip, request_path(request))

    token_pair = _create_token_pair(
        user_id=user.id,
        scopes=user.scopes,
        classification=getattr(user, "classification", "UNCLASSIFIED"),
    )

    await _log_audit(
        user_id=user.id,
        action="LOGIN",
        resource="user",
        resource_id=user.id,
        ip=client_ip,
        db_session=db,
    )

    await event_bus.publish("user.login", {
        "user_id": user.id,
        "username": user.username,
        "ip": client_ip,
    })

    return LoginResponse(
        mfa_required=False,
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: DBSession,
) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    path = request_path(request)

    if await BruteForceProtector.is_locked(body.username, path):
        remaining = await BruteForceProtector.get_remaining_attempts(body.username, path)
        from app.core.metrics import record_security_event
        record_security_event("brute_force_lockout", "auth")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked. Remaining attempts: {remaining}",
        )

    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        await BruteForceProtector.record_failure(body.username, client_ip, path)
        remaining = await BruteForceProtector.get_remaining_attempts(body.username, path)
        from app.core.metrics import record_security_event
        record_security_event("auth_failure", "auth")

        await _log_audit(
            user_id="unknown",
            action="LOGIN",
            resource="user",
            resource_id=body.username,
            ip=client_ip,
            success=False,
            error="Invalid credentials",
            db_session=db,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials. Remaining attempts: {remaining}",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    if getattr(user, "mfa_enabled", False) and getattr(user, "mfa_secret", None):
        ticket = _issue_mfa_ticket(user.id)
        await _log_audit(
            user_id=user.id,
            action="LOGIN",
            resource="user",
            resource_id=user.id,
            ip=client_ip,
            details={"step": "password_ok_mfa_pending"},
            db_session=db,
        )
        return LoginResponse(mfa_required=True, mfa_ticket=ticket)

    return await _issue_tokens_for(user, request, db, client_ip)


@router.post("/mfa/verify", response_model=LoginResponse)
async def mfa_verify(
    request: Request,
    body: MfaVerifyRequest,
    db: DBSession,
) -> LoginResponse:
    client_ip = request.client.host if request.client else "unknown"
    try:
        payload = await _verify_mfa_ticket(body.mfa_ticket)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA ticket",
        )

    user = (
        await db.execute(select(User).where(User.id == payload["sub"]))
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not getattr(user, "mfa_enabled", False) or not getattr(user, "mfa_secret", None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not enabled for user")

    if not _verify_code(user.mfa_secret, body.code):
        await BruteForceProtector.record_failure(user.username, client_ip, request_path(request))
        await _log_audit(
            user_id=user.id,
            action="LOGIN",
            resource="user",
            resource_id=user.id,
            ip=client_ip,
            success=False,
            error="Invalid MFA code",
        db_session=db,
    )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    return await _issue_tokens_for(user, request, db, client_ip)


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def mfa_setup(user: CurrentUser) -> MfaSetupResponse:
    secret = _generate_secret()
    return MfaSetupResponse(
        secret=secret,
        otpauth_uri=_provisioning_uri(secret, account=user.username),
    )


@router.post("/mfa/enable", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def mfa_enable(
    request: Request,
    body: MfaEnableRequest,
    user: CurrentUser,
    db: DBSession,
) -> None:
    raw_secret = request.headers.get("x-mfa-secret", "").strip()
    if not raw_secret or not body.code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing secret or code")

    encrypted = _encrypt_secret(raw_secret)
    if not _verify_code(raw_secret, body.code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code does not match secret")

    await db.execute(
        update(User).where(User.id == user.id).values(mfa_enabled=True, mfa_secret=encrypted)
    )
    await db.commit()

    await _log_audit(
        user_id=user.id,
        action="MFA_ENABLE",
        resource="user",
        resource_id=user.id,
        ip=request.client.host if request.client else "",
        db_session=db,
    )


@router.post("/mfa/disable", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def mfa_disable(
    request: Request,
    body: MfaEnableRequest,
    user: CurrentUser,
    db: DBSession,
) -> None:
    if not getattr(user, "mfa_enabled", False) or not getattr(user, "mfa_secret", None):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="MFA not enabled")

    if not _verify_code(user.mfa_secret, body.code):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    await db.execute(
        update(User).where(User.id == user.id).values(mfa_enabled=False, mfa_secret=None)
    )
    await db.commit()

    await _log_audit(
        user_id=user.id,
        action="MFA_DISABLE",
        resource="user",
        resource_id=user.id,
        ip=request.client.host if request.client else "",
        db_session=db,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: TokenRefresh, db: DBSession) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    blacklist = await get_token_blacklist()
    if await blacklist.is_blacklisted(payload.get("jti", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    token_pair = _create_token_pair(
        user_id=user.id,
        scopes=user.scopes,
        session_id=payload.get("sid", ""),
    )

    return TokenResponse(
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
        token_type=token_pair.token_type,
        expires_in=token_pair.expires_in,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def logout(
    request: Request,
    user: CurrentUser,
    db: DBSession,
    body: TokenRefresh | None = None,
) -> None:
    blacklist = await get_token_blacklist()

    auth_header = request.headers.get("authorization", "")
    sid = ""
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        try:
            payload = decode_token(access_token)
            sid = payload.get("sid", "") or ""
            exp = payload.get("exp", 0)
            jti = payload.get("jti", "")
            if jti:
                await blacklist.add(jti, exp)
        except HTTPException:
            pass

    if body and body.refresh_token:
        try:
            rpayload = decode_token(body.refresh_token)
            if rpayload.get("type") == "refresh" and rpayload.get("sub") == user.id:
                exp = rpayload.get("exp", 0)
                jti = rpayload.get("jti", "")
                if jti:
                    await blacklist.add(jti, exp)
        except HTTPException:
            pass

    await _log_audit(
        user_id=user.id,
        action="LOGOUT",
        resource="user",
        resource_id=user.id,
        ip=request.client.host if request.client else "",
        db_session=db,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: CurrentUser) -> User:
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def change_password(
    body: PasswordChange,
    user: CurrentUser,
    db: DBSession,
) -> None:
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password incorrect")

    issues = _validate_password_strength(body.new_password)
    if issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "issues": issues},
        )

    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(hashed_password=hash_password(body.new_password))
    )
    await db.commit()


async def _create_user(db: AsyncSession, body: UserCreate, request: Request, *, created_by: str) -> User:
    issues = _validate_password_strength(body.password)
    if issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "issues": issues},
        )

    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    existing_email = await db.execute(select(User).where(User.email == body.email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name or "",
        scopes=["read:cases", "write:cases", "execute:jobs"],
        classification=getattr(body, "classification", "UNCLASSIFIED"),
        tenant_id=getattr(body, "tenant_id", "default") or "default",
        department=getattr(body, "department", None),
        phone=getattr(body, "phone", None),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await _log_audit(
        user_id=created_by,
        action="USER_CREATE",
        resource="user",
        resource_id=user.id,
        ip=request.client.host if request.client else "",
        db_session=db,
    )
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: UserCreate,
    db: DBSession,
    request: Request,
    admin: AdminUser,
) -> User:
    return await _create_user(db, body, request, created_by=admin.id)


@router.post(
    "/bootstrap-admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bootstrap_admin(
    body: UserCreate,
    db: DBSession,
    request: Request,
) -> User:
    existing_any = await db.execute(select(User).limit(1))
    if existing_any.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bootstrap already complete; use POST /auth/register (admin-only)",
        )

    issues = _validate_password_strength(body.password)
    if issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Password does not meet requirements", "issues": issues},
        )

    admin_scopes = sorted({
        "admin", "read:cases", "write:cases", "read:reports", "write:reports",
        "read:evidence", "write:evidence", "read:entities", "write:entities",
        "read:users", "write:users", "execute:jobs", "audit:log", "system:config",
    })

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name or "Bootstrap Admin",
        is_active=True,
        is_superuser=True,
        scopes=admin_scopes,
        classification=getattr(body, "classification", "TOP_SECRET") or "TOP_SECRET",
        tenant_id=getattr(body, "tenant_id", "default") or "default",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await _log_audit(
        user_id=user.id,
        action="BOOTSTRAP_ADMIN",
        resource="user",
        resource_id=user.id,
        ip=request.client.host if request.client else "",
        db_session=db,
    )
    return user


@router.post("/revoke-all-tokens", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def revoke_all_tokens(
    user: CurrentUser,
    db: DBSession,
) -> None:
    blacklist = await get_token_blacklist()
    await blacklist.revoke_all_user_tokens(user.id, 9999999999.0)
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.now(timezone.utc))
    )
    await db.commit()
