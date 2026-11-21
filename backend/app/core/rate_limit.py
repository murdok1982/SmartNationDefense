"""
Rate Limiting Middleware - Sliding Window con Redis.
Protege contra DDoS y abuso de API en sistemas militares.
"""
import asyncio
import time
import hashlib
import uuid
from fastapi import Request, status
from fastapi.responses import JSONResponse
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
        "login": (5, 60),
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
        if path.rstrip("/").endswith("/auth/login"):
            limit_key = "login"
        elif "/brain/" in path:
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
        try:
            allowed, info = await self.limiter.is_allowed(key, max_req, window)
        except Exception as e:
            logger.error(f"Rate limiter no disponible ({e}); peticion permitida")
            return await call_next(request)

        if not allowed:
            logger.warning(f"Rate limit excedido: {client_ip} en {path}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": f"Rate limit excedido. Reintente en {info['retry_after']}s"},
                headers={"Retry-After": str(info["retry_after"])},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        return response


# ---------------------------------------------------------------------------
# Path-aware rate-limit key (TASK-012)
# ---------------------------------------------------------------------------


def get_limiter_key(user, path: str = "") -> str:
    """
    Construye una key de rate-limit que incluye el path: user + endpoint.

    Los contadores del protector brute-force (lockout, bf_attempts)
    quedan path-aware: el mismo usuario tiene budgets separados por
    endpoint (login, mfa/verify, ...) en lugar de compartir uno solo
    por username.
    """
    safe_path = (path or "").rstrip("/") or "/"
    return f"{user}:{safe_path}"


# ---------------------------------------------------------------------------
# Circuit breaker fail-open (TASK-013)
# ---------------------------------------------------------------------------


class CircuitBreaker:
    """
    Circuit breaker para rate limits: se abre tras múltiples fallos y
    deniega peticiones mientras está abierto.

    Estado: OPEN, HALF_OPEN, CLOSED.

    - CLOSED: se cuentan requests en rl:count:{key}. El circuito se abre
      si (a) requests > max_requests en la ventana, O (b) failures/attempts
      >= failure_limit en la ventana -> setex OPEN con TTL*2, deniega.
    - OPEN: se deniega mientras falta el TTL; al expirar -> HALF_OPEN.
    - HALF_OPEN: permite request de prueba; si hay éxito -> CLOSED.

    Si Redis no está disponible, el circuito falla open (se permite).

    Keys: rl:count:{key} (ZSET de timestamps), rl:failures:{key} (ZSET),
    rl:state:{key} (OPEN|HALF_OPEN|CLOSED, con TTL cuando está OPEN).
    """

    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"
    CLOSED = "CLOSED"

    def __init__(self, redis_client=None, window_seconds: int = 60, failure_limit: int = 5):
        self.redis = redis_client
        self.window_seconds = window_seconds
        self.failure_limit = failure_limit

    # -- helpers sincrónicos (soporta clientes sync y async) -------------

    def _call(self, func, *args, **kwargs):
        """
        Llama a un método del cliente Redis devolviendo el valor
        síncrono. Soporta clientes async (redis.asyncio): si el resultado
        es un coroutine se resuelve con un bucle nuevo.
        """
        value = func(*args, **kwargs)
        if asyncio.iscoroutine(value):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(value)
            value.close()
            raise RuntimeError("CircuitBreaker: cliente async dentro de un bucle corriendo")
        return value

    def _set(self, key: str, value: str) -> None:
        if self.redis is None:
            return
        self._call(self.redis.set, key, value)

    def _setex(self, key: str, value: str, ttl: int) -> None:
        if self.redis is None:
            return
        self._call(self.redis.setex, key, int(ttl), value)

    def _ttl(self, key: str) -> int:
        if self.redis is None:
            return 0
        return self._call(self.redis.ttl, key) or 0

    def _count(self, key: str, failures: bool = False, window_seconds: int = 60) -> int:
        zkey = f"rl:failures:{key}" if failures else f"rl:count:{key}"
        if self.redis is None:
            return 0
        now = time.time()
        self._call(self.redis.zremrangebyscore, zkey, "-inf", now - window_seconds)
        return self._call(self.redis.zcard, zkey) or 0

    def _record_request(self, key: str, window_seconds: int = 60) -> None:
        if self.redis is None:
            return
        now = time.time()
        member = f"{now}:{uuid.uuid4().hex[:8]}"
        self._call(self.redis.zadd, f"rl:count:{key}", {member: now})
        self._call(self.redis.expire, f"rl:count:{key}", window_seconds)

    # -- API pública -----------------------------------------------------

    def check(
        self,
        key,
        max_requests: int = 100,
        window_seconds: int = 60,
        failure_limit: int = 5,
        base_key=None,
    ) -> bool:
        """
        Devuelve True (permitido) / False (denegado). Fail-open: sin Redis
        siempre True.
        """
        base = base_key or key
        state_key = f"rl:state:{base}"
        try:
            state = self._call(self.redis.get, state_key) if self.redis else None
            state = state if state in (self.OPEN, self.HALF_OPEN, self.CLOSED) else self.CLOSED

            if state == self.OPEN:
                if self._ttl(state_key) > 0:
                    return False  # OPEN: denegar mientras falta el TTL
                self._set(state_key, self.HALF_OPEN)  # falta ttl -> HALF_OPEN
                state = self.HALF_OPEN

            if state in (self.CLOSED, self.HALF_OPEN):
                # (a) requests > max_requests en la ventana
                if self._count(base, failures=False, window_seconds=window_seconds) > max_requests:
                    self._setex(state_key, self.OPEN, window_seconds * 2)
                    return False
                # (b) failures/attempts >= failure_limit en la ventana
                if self._count(base, failures=True, window_seconds=window_seconds) >= failure_limit:
                    self._setex(state_key, self.OPEN, window_seconds * 2)
                    return False
                # dentro del window -> permitir
                self._record_request(base, window_seconds)
                return True
            return True
        except Exception:
            return True  # fail-open

    def report_failure(self, key, failure_threshold: int = 5) -> None:
        """Incrementa rl:failures:{key}; abre el circuito si >= threshold."""
        base = key
        try:
            if self.redis is None:
                return
            now = time.time()
            member = f"{now}:{uuid.uuid4().hex[:8]}"
            self._call(self.redis.zadd, f"rl:failures:{base}", {member: now})
            if self._count(base, failures=True, window_seconds=self.window_seconds) >= failure_threshold:
                self._setex(f"rl:state:{base}", self.OPEN, self.window_seconds * 2)
        except Exception:
            pass

    def report_success(self, key) -> None:
        """zrem range del failures; estado CLOSED; quita lock."""
        base = key
        try:
            if self.redis is None:
                return
            now = time.time()
            self._call(self.redis.zremrangebyscore, f"rl:failures:{base}", "-inf", "+inf")
            self._set(f"rl:state:{base}", self.CLOSED)
        except Exception:
            pass
