# -*- coding: utf-8 -*-
"""Bus de eventos unificado (NATS + fallback en memoria).

Incluye, desde TASK-028:
  * **Idempotencia de publicación**: cada mensaje lleva un ``msg_id``; las
    republicaciones del mismo id se suprimen (Redis ``SETNX`` con TTL o
    almacén en memoria si Redis no está disponible).
  * **Dead Letter Queue (DLQ)**: los consumidores reintentan hasta
    ``MAX_DELIVERY_ATTEMPTS``; al agotarse, el mensaje se publica en la DLQ
    (``<subject>.dlq`` + registro en ``nats:dlq:<subject>``).
  * **Ack/Nak explícito**: los consumidores NATS confirman (``ack``) los
    mensajes procesados y marcan ``nak`` los fallidos.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_SECONDS = 3600


class EventBus:
    """Event bus NATS con fallback en memoria, idempotencia y DLQ."""

    MAX_DELIVERY_ATTEMPTS = 3
    DLQ_SUFFIX = ".dlq"

    def __init__(self):
        self.nc = None
        self.js = None
        self.subscribers: Dict[str, list] = {}
        self._idempotency: Dict[str, float] = {}
        self.dead_letters: list[dict[str, Any]] = []
        self._idempotency_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------
    async def connect(self):
        try:
            import nats
            from app.core.config import settings

            self.nc = await nats.connect(settings.NATS_URL)
            self.js = self.nc.jetstream()
            logger.info("Connected to NATS at %s", settings.NATS_URL)
        except ImportError:
            logger.warning("nats-py not installed — using in-memory event bus")
        except Exception as e:
            logger.error("NATS connection failed: %s", e)

    async def disconnect(self):
        if self.nc:
            await self.nc.drain()
            self.nc = None

    # ------------------------------------------------------------------
    # Idempotencia
    # ------------------------------------------------------------------
    async def _claim_idempotency(self, msg_id: str, ttl: int = IDEMPOTENCY_TTL_SECONDS) -> bool:
        """Devuelve True si el mensaje es nuevo; False si es un duplicado."""
        redis_client = None
        try:
            from app.db.redis_pool import get_redis_pool

            redis_client = await get_redis_pool()
        except Exception:
            redis_client = None

        key = f"nats:idem:{msg_id}"
        if redis_client is not None:
            try:
                claimed = await redis_client.set(key, "1", ex=ttl, nx=True)
                return bool(claimed)
            except Exception as exc:  # pragma: no cover - degradación defensiva
                logger.warning("Idempotency check failed in Redis (%s); using memory store", exc)

        async with self._idempotency_lock:
            now = time.monotonic()
            # limpieza perezosa
            expired = [k for k, exp in self._idempotency.items() if exp <= now]
            for k in expired:
                self._idempotency.pop(k, None)
            if msg_id in self._idempotency:
                return False
            self._idempotency[msg_id] = now + ttl
            return True

    # ------------------------------------------------------------------
    # Publicación
    # ------------------------------------------------------------------
    async def publish(
        self,
        subject: str,
        data: Dict[str, Any],
        *,
        msg_id: Optional[str] = None,
        idempotent: bool = True,
    ) -> bool:
        """Publica un evento. Devuelve False si fue suprimido por idempotencia."""
        envelope = dict(data)
        msg_id = msg_id or envelope.get("id") or envelope.get("msg_id") or str(uuid.uuid4())
        envelope.setdefault("msg_id", msg_id)
        envelope.setdefault("subject", subject)

        if idempotent and not await self._claim_idempotency(msg_id):
            logger.info("Duplicate event suppressed: %s (%s)", subject, msg_id)
            return False

        if self.nc:
            await self.nc.publish(subject, json.dumps(envelope).encode())
        for cb in list(self.subscribers.get(subject, [])):
            await self._deliver(subject, cb, envelope)
        return True

    async def _deliver(self, subject: str, callback: Callable, data: Dict[str, Any], msg=None) -> None:
        """Entrega con reintentos; al agotarse mueve el mensaje a la DLQ."""
        last_error: Exception | None = None
        for attempt in range(1, self.MAX_DELIVERY_ATTEMPTS + 1):
            try:
                await callback(data)
                if msg is not None:
                    await msg.ack()
                return
            except Exception as exc:  # noqa: BLE001 - el fallo del consumidor es esperado
                last_error = exc
                logger.warning(
                    "Event delivery failed (%s) attempt %d/%d: %s",
                    subject, attempt, self.MAX_DELIVERY_ATTEMPTS, exc,
                )
        if msg is not None:
            await msg.nak()
        await self.publish_dlq(subject, data, reason=str(last_error), attempts=self.MAX_DELIVERY_ATTEMPTS)

    # ------------------------------------------------------------------
    # Dead Letter Queue
    # ------------------------------------------------------------------
    async def publish_dlq(
        self,
        subject: str,
        data: Dict[str, Any],
        *,
        reason: str = "",
        attempts: int = 0,
    ) -> bool:
        entry = {
            "subject": subject,
            "data": data,
            "reason": reason,
            "attempts": attempts,
            "ts": time.time(),
        }
        self.dead_letters.append(entry)
        if len(self.dead_letters) > 1000:
            self.dead_letters = self.dead_letters[-1000:]

        if self.nc:
            try:
                await self.nc.publish(f"{subject}{self.DLQ_SUFFIX}", json.dumps(entry).encode())
            except Exception as exc:  # pragma: no cover - defensivo
                logger.error("Failed to publish to NATS DLQ: %s", exc)

        try:
            from app.db.redis_pool import get_redis_pool

            redis_client = await get_redis_pool()
            if redis_client is not None:
                await redis_client.zadd(f"nats:dlq:{subject}", {json.dumps(entry): entry["ts"]})
                await redis_client.zremrangebyscore(f"nats:dlq:{subject}", "-inf", entry["ts"] - 86400)
        except Exception as exc:  # pragma: no cover - defensivo
            logger.debug("Redis DLQ unavailable: %s", exc)

        logger.error("Event moved to DLQ: %s (reason=%s, attempts=%d)", subject, reason, attempts)
        return True

    async def subscribe(self, subject: str, callback: Callable):
        self.subscribers.setdefault(subject, []).append(callback)
        if self.nc:
            async def _handler(msg):
                try:
                    payload = json.loads(msg.data)
                except Exception:
                    await msg.term()
                    await self.publish_dlq(subject, {"raw": msg.data.decode(errors="replace")}, reason="invalid json")
                    return
                await self._deliver(subject, callback, payload, msg=msg)

            await self.nc.subscribe(subject, cb=_handler)


event_bus = EventBus()
