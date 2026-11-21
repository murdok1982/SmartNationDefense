# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    revoke_jti,
    is_jti_revoked,
)
from app.db.session import get_db

router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=8, max_length=128)
    email: Optional[str] = Field(None, max_length=255)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str]
    role: str
    classification_level: str
    is_active: bool


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Login con lockout distribuido (SEC-FIX-005).

    El protector de fuerza bruta vive en Redis y es path-aware: el contador
    de `/api/v1/auth/login` no se mezcla con el de MFA u otros endpoints.
    """
    from app.api.osint.auth import BruteForceProtector, _log_audit
    from app.core.rate_limit import request_path, resolve_client_ip

    client_ip = resolve_client_ip(request)
    # SEC-FIX-009: scope["path"], no request.url.path (poisonable vía Host).
    path = request_path(request)

    if await BruteForceProtector.is_locked(payload.username, path):
        remaining = await BruteForceProtector.get_remaining_attempts(payload.username, path)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Cuenta bloqueada temporalmente. Intentos restantes: {remaining}",
            headers={"Retry-After": "60"},
        )

    from app.db.models.persistence import User
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalars().first()
    if not user or not verify_password(payload.password, user.hashed_password):
        await BruteForceProtector.record_failure(payload.username, client_ip, path)
        await _log_audit(
            user_id="unknown",
            action="LOGIN",
            resource="user",
            resource_id=payload.username,
            ip=client_ip,
            success=False,
            error="Invalid credentials",
            db_session=db,
        )
        from app.core.metrics import record_security_event
        record_security_event("auth_failure", "auth")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    await BruteForceProtector.record_success(payload.username, client_ip, path)

    token_data = {"sub": user.id, "username": user.username, "role": user.role, "clearance": user.classification_level}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registro de operadores: la cuenta queda INACTIVA (is_active=False)
    hasta que un administrador la apruebe. Opcion elegida por ser la menos
    disruptiva: el endpoint sigue siendo publico pero no concede acceso."""
    from app.db.models.persistence import User
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya existe",
        )

    user = User(
        id=str(uuid.uuid4()),
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="operator",
        classification_level="RESTRICTED",
        is_active=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        classification_level=user.classification_level,
        is_active=user.is_active,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Rota el par de tokens: verifica el jti contra la blacklist y revoca
    el refresh token usado antes de emitir uno nuevo."""
    from app.db.models.persistence import User
    data = decode_token(payload.refresh_token, is_refresh=True)
    if await is_jti_revoked(data.get("jti")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revocado",
        )

    result = await db.execute(select(User).where(User.id == data.get("sub")))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario invalido o inactivo",
        )

    if data.get("jti"):
        await revoke_jti(data["jti"], data.get("exp", 0))

    token_data = {"sub": user.id, "username": user.username, "role": user.role, "clearance": user.classification_level}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


@router.post("/logout")
async def logout(
    payload: Optional[LogoutRequest] = None,
    current_user: dict = Depends(get_current_user),
):
    """Revoca el access token actual (jti) y, si se suministra, el refresh token."""
    jti = current_user.get("jti")
    if jti:
        await revoke_jti(jti, current_user.get("exp", 0))

    if payload and payload.refresh_token:
        try:
            data = decode_token(payload.refresh_token, is_refresh=True)
            if data.get("jti"):
                await revoke_jti(data["jti"], data.get("exp", 0))
        except HTTPException:
            pass

    return {"detail": "Sesion cerrada correctamente"}


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.db.models.persistence import User
    user_id = current_user.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        classification_level=user.classification_level,
        is_active=user.is_active,
    )
