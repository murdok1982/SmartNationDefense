"""
Rate Limiting Middleware - Sliding Window con Redis.
Protege contra DDoS y abuso de API en sistemas militares.
"""
import time
import hashlib
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger("sesis.security.ratelimit")


class SlidingWindowRateLimiter:
    """
    Rate limiter usando algoritmo Sliding Window con Redis async.
    Mas preciso que Fixed Window, evita burst al cambio de ventana.
    """

    def __init__(self, redis_client, prefix: str = "ratelimit:"):
        self.redis = redis_client
        self.prefix = prefix

    async def is_allowed(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, Dict[str, Any]]:
        now = time.time()
        window_start = now - window_seconds
        redis_key = f"{self.prefix}{key}"

        await self.redis.zremrangebyscore(redis_key, "-inf", window_start)
        current_count = await self.redis.zcard(redis_key)

        if current_count >= max_requests:
            oldest = await self.redis.zrange(redis_key, 0, 0, withscores=True)
            retry_after = int(oldest[0][1] - window_start) if oldest else window_seconds
            return False, {
                "allowed": False,
                "limit": max_requests,
                "remaining": 0,
                "retry_after": retry_after
            }

        import uuid
        await self.redis.zadd(redis_key, {f"{now}:{uuid.uuid4().hex[:8]}": now})
        await self.redis.expire(redis_key, window_seconds)

        return True, {
            "allowed": True,
            "limit": max_requests,
            "remaining": max_requests - current_count - 1,
            "retry_after": 0
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware FastAPI para rate limiting por IP o API Key.
    Configuracion por endpoint y nivel de clasificacion.
    """

    DEFAULT_LIMITS = {
        "default": (100, 60),
        "brain": (20, 60),
        "ingest": (500, 60),
        "classified": (50, 60),
    }

    def __init__(self, app, redis_client):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(redis_client)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next: Callable):
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        key_parts = [client_ip]
        if api_key:
            key_parts.append(hashlib.sha256(api_key.encode()).hexdigest()[:16])

        path = request.url.path
        limit_key = "default"
        if "/brain/" in path:
            limit_key = "brain"
        elif "/ingest" in path:
            limit_key = "ingest"

        max_req, window = self.DEFAULT_LIMITS.get(
            limit_key, self.DEFAULT_LIMITS["default"]
        )

        clearance = getattr(request.state, "clearance", "OPEN")
        if clearance in ["SECRET", "TOP_SECRET"]:
            max_req = self.DEFAULT_LIMITS["classified"][0]

        key = f"{limit_key}:{':'.join(key_parts)}"
        allowed, info = await self.limiter.is_allowed(key, max_req, window)

        if not allowed:
            logger.warning(f"Rate limit excedido: {client_ip} en {path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit excedido. Reintente en {info['retry_after']}s",
                headers={"Retry-After": str(info["retry_after"])}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        return response
