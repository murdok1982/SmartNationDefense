# -*- coding: utf-8 -*-
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decode_token

logger = logging.getLogger(__name__)

PUBLIC_PATHS = {
    "/",
    "/health",
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """Establece request.state.principal a partir del Bearer token.

    Falla abierto: nunca bloquea la peticion; el bloqueo lo aplican las
    dependencias (require_clearance / get_current_user) en cada endpoint.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.principal = None
        if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:].strip()
            try:
                payload = decode_token(token)
                request.state.principal = payload
                request.state.clearance = payload.get("clearance", "OPEN")
            except Exception:
                logger.warning(
                    "Token JWT invalido o expirado desde %s",
                    request.client.host if request.client else "desconocido",
                )
        return await call_next(request)
