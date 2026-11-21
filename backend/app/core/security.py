# -*- coding: utf-8 -*-
import hashlib
import logging
import time
import uuid
import warnings
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, List, Tuple

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_scheme = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def create_access_token(
    data: dict | str,
    expires_delta: Optional[timedelta] = None,
    **extra_claims: Any,
) -> str:
    if isinstance(data, str):
        to_encode: dict = {"sub": data}
    else:
        to_encode = data.copy()
    to_encode.update(extra_claims)
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "jti": uuid.uuid4().hex,
        "aud": settings.JWT_AUDIENCE,
        "iss": settings.JWT_ISSUER,
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def create_mfa_challenge_token(
    data: dict | str,
    expires_delta: Optional[timedelta] = None,
    **extra_claims: Any,
) -> str:
    """Issues a short-lived single-use MFA challenge ticket with explicit type 'mfa_challenge'."""
    if isinstance(data, str):
        to_encode: dict = {"sub": data}
    else:
        to_encode = data.copy()
    to_encode.update(extra_claims)
    ttl = expires_delta or timedelta(seconds=getattr(settings, "MFA_CHALLENGE_TTL_SECONDS", 300))
    expire = datetime.now(timezone.utc) + ttl
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "mfa_challenge",
        "jti": uuid.uuid4().hex,
        "aud": settings.JWT_AUDIENCE,
        "iss": settings.JWT_ISSUER,
    })
    secret = getattr(settings, "MFA_CHALLENGE_SECRET", "") or settings.SECRET_KEY
    if not getattr(settings, "MFA_CHALLENGE_SECRET", ""):
        warnings.warn(
            "MFA_CHALLENGE_SECRET no esta configurado; el ticket MFA usa SECRET_KEY como fallback "
            "(debilita el aislamiento del ticket)",
            stacklevel=2,
        )
    return jwt.encode(to_encode, secret, algorithm="HS256")


def decode_mfa_token(token: str) -> dict:
    """Decodes and validates an MFA challenge ticket. Strictly rejects any other token type."""
    secret = getattr(settings, "MFA_CHALLENGE_SECRET", "") or settings.SECRET_KEY
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        if payload.get("type") != "mfa_challenge":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type: expected mfa_challenge",
            )
        header_getter = getattr(jwt, "get_unverified_header", None)
        if header_getter is not None and header_getter(token).get("alg") != "HS256":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA challenge token con algoritmo invalido",
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA challenge token invalido o expirado",
        )


def create_refresh_token(
    data: dict | str,
    **extra_claims: Any,
) -> str:
    if isinstance(data, str):
        to_encode: dict = {"sub": data}
    else:
        to_encode = data.copy()
    to_encode.update(extra_claims)
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "aud": settings.JWT_AUDIENCE,
        "iss": settings.JWT_ISSUER,
    })
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str, is_refresh: bool = False, expected_type: Optional[str] = None) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        target_type = expected_type or ("refresh" if is_refresh else "access")
        if payload.get("type") != target_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type: expected {target_type}, got {payload.get('type')}",
            )
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado")


async def revoke_jti(jti: str, exp: int) -> None:
    """Registra un jti en la blacklist de Redis hasta su expiracion natural."""
    try:
        from app.db.redis_pool import get_redis_pool
        redis_client = await get_redis_pool()
        ttl = max(1, int(exp) - int(time.time()))
        await redis_client.setex(f"revoked:{jti}", ttl, "1")
    except Exception as e:
        logger.warning(f"No se pudo registrar la revocacion del token: {e}")


async def is_jti_revoked(jti: Optional[str]) -> bool:
    if not jti:
        return False
    try:
        from app.db.redis_pool import get_redis_pool
        redis_client = await get_redis_pool()
        return bool(await redis_client.exists(f"revoked:{jti}"))
    except Exception as e:
        logger.warning(f"No se pudo verificar la revocacion del token: {e}")
        from app.core.metrics import record_fail_open
        record_fail_open("jti_revocation")
        if settings.security_fail_closed:
            # SEC-FIX-001: no se puede demostrar que el token no está revocado.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Servicio de verificacion de tokens no disponible",
            )
        return False


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("type") in ("mfa_challenge", "challenge"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    if await is_jti_revoked(payload.get("jti")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revocado")
    return payload


CLEARANCE_ORDER = {
    "OPEN": 0,
    "RESTRICTED": 1,
    "CONFIDENTIAL": 2,
    "SECRET": 3,
    "TOP_SECRET": 4,
}


class ABACEngine:
    LEVEL_HIERARCHY = {"public": 0, "restricted": 1, "confidential": 2, "secret": 3, "top_secret": 4}

    def __init__(self):
        self.policies = {}

    def register_policy(self, resource: str, required_level: str):
        self.policies[resource] = required_level

    def check_access(self, request: Request, resource: str) -> bool:
        principal = getattr(request.state, "principal", None)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: JWT token missing or invalid",
            )
        user_level = principal.get("clearance", "public").lower()
        required = self.policies.get(resource, "public").lower()
        user_lvl = self.LEVEL_HIERARCHY.get(user_level, 0)
        req_lvl = self.LEVEL_HIERARCHY.get(required, 0)
        if user_lvl < req_lvl:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient clearance: need {required}, have {user_level}",
            )
        return True


abac = ABACEngine()


def require_clearance(min_level: str):
    async def dep(request: Request) -> dict:
        principal = getattr(request.state, "principal", None)
        if principal is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: JWT token missing, invalid, or expired",
            )
        subj = CLEARANCE_ORDER.get(principal.get("clearance", "OPEN"), 0)
        need = CLEARANCE_ORDER.get(min_level, 0)
        if subj < need:
            from app.core.metrics import record_security_event
            record_security_event("clearance_denied", "security")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"clearance < {min_level}",
            )
        return principal
    return dep


class TokenPayload(BaseModel):
    sub: str
    exp: int
    iat: int
    type: str
    roles: List[str] = []
    clearance: str = "OPEN"
    mfa: bool = False
    jti: Optional[str] = None
    aud: Optional[str] = None
    iss: Optional[str] = None


class JWTService:
    def __init__(self, secret_key: str, algorithm: str = "HS256",
                 access_expire_min: int = 15, refresh_expire_days: int = 7):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_expire = timedelta(minutes=access_expire_min)
        self.refresh_expire = timedelta(days=refresh_expire_days)

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_access_token(
        self,
        subject: str,
        roles: Optional[list[str]] = None,
        clearance: str = "OPEN",
        mfa_verified: bool = False,
    ) -> str:
        expire = datetime.now(timezone.utc) + self.access_expire
        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access",
            "mfa": mfa_verified,
            "roles": roles or [],
            "clearance": clearance,
            "aud": "sesis-c2",
            "iss": "sesis-auth-server"
        }
        return jwt.encode(payload, self.secret_key, self.algorithm)

    def create_refresh_token(self, subject: str, redis_client=None) -> str:
        import uuid as _uuid
        expire = datetime.now(timezone.utc) + self.refresh_expire
        jti = _uuid.uuid4().hex
        payload = {
            "sub": subject,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "refresh",
            "aud": "sesis-c2",
            "iss": "sesis-auth-server",
            "jti": jti,
        }
        token = jwt.encode(payload, self.secret_key, self.algorithm)
        if redis_client:
            redis_key = f"refresh:{subject}"
            redis_client.setex(redis_key, int(self.refresh_expire.total_seconds()), self._hash_token(token))
        return token

    def decode_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
            )
            return TokenPayload(**payload)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalido o expirado"
            )

    def verify_refresh_token(self, token: str, redis_client=None) -> TokenPayload:
        payload = self.decode_token(token)
        if payload.type != "refresh":
            raise HTTPException(status_code=400, detail="No es un refresh token")

        if redis_client:
            if payload.jti and redis_client.exists(f"revoked:{payload.jti}"):
                raise HTTPException(status_code=401, detail="Refresh token revocado")

            redis_key = f"refresh:{payload.sub}"
            stored = redis_client.get(redis_key)
            if not stored:
                raise HTTPException(status_code=401, detail="Refresh token revocado o invalido")
            stored_str = stored.decode() if isinstance(stored, (bytes, bytearray)) else stored
            if stored_str != self._hash_token(token):
                raise HTTPException(status_code=401, detail="Refresh token revocado o invalido")

            if payload.jti:
                remaining = max(1, payload.exp - int(time.time()))
                redis_client.setex(f"revoked:{payload.jti}", remaining, "1")
            redis_client.delete(redis_key)

        return payload

    def rotate_tokens(
        self,
        token: str,
        redis_client=None,
        roles: Optional[list[str]] = None,
        clearance: str = "OPEN",
        mfa_verified: bool = False,
    ) -> Tuple[str, str]:
        payload = self.verify_refresh_token(token, redis_client)
        new_access = self.create_access_token(
            subject=payload.sub,
            roles=roles or payload.roles,
            clearance=clearance or payload.clearance,
            mfa_verified=mfa_verified or payload.mfa,
        )
        new_refresh = self.create_refresh_token(payload.sub, redis_client)
        return new_access, new_refresh

    def revoke_refresh_token(self, subject: str, redis_client=None) -> None:
        if redis_client:
            redis_client.delete(f"refresh:{subject}")
