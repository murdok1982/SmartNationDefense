# -*- coding: utf-8 -*-
import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class AuditChain:
    """Tamper-evident audit chain with SHA-256 hash chaining and async concurrency locking.

    Note: Cryptographic hash chaining provides tamper evidence, but does not equal
    physical immutability unless combined with external WORM storage or append-only
    remote log shipping.
    """

    def __init__(self):
        self.last_hash: Optional[str] = None
        self._lock = asyncio.Lock()

    async def record(
        self,
        event: str,
        actor: str,
        resource: str,
        classification: str = "restricted",
        details: Optional[Dict[str, Any]] = None,
        db_session=None,
    ) -> Dict[str, Any]:
        async with self._lock:
            # Rehydrate last_hash from database if not yet initialized in this process
            if self.last_hash is None and db_session is not None:
                try:
                    from sqlalchemy import select
                    from app.db.models.persistence import AuditLog
                    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(1)
                    res = await db_session.execute(stmt)
                    last_row = res.scalars().first()
                    if last_row and getattr(last_row, "row_hash", None):
                        self.last_hash = last_row.row_hash
                except Exception as e:
                    logger.debug("Could not recover latest audit hash from DB: %s", e)

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "actor": actor,
                "resource": resource,
                "classification": classification,
                "details": details or {},
                "previous_hash": self.last_hash or "0" * 64,
            }
            entry["hash"] = self._compute_hash(entry)

            if self.last_hash and entry["previous_hash"] != self.last_hash:
                logger.error(f"Audit chain integrity violation at {entry['timestamp']}")
                raise ValueError("Audit chain integrity violated: previous hash mismatch")

            self.last_hash = entry["hash"]

            if db_session:
                try:
                    from app.db.models.persistence import AuditLog
                    log = AuditLog(
                        ts=datetime.fromisoformat(entry["timestamp"]),
                        actor=actor,
                        action=event,
                        resource_type=resource.split(":")[0] if ":" in resource else resource,
                        resource_id=resource.split(":", 1)[1] if ":" in resource else "",
                        context=details or {},
                        prev_hash=entry["previous_hash"],
                        row_hash=entry["hash"],
                        user_id=str(actor),
                        username=(details or {}).get("username", ""),
                        details=details or {},
                        ip_address=(details or {}).get("ip", ""),
                        user_agent=(details or {}).get("user_agent", ""),
                        request_id=(details or {}).get("request_id", ""),
                        success=bool((details or {}).get("success", True)),
                        error_message=(details or {}).get("error") or "",
                    )
                    db_session.add(log)
                    await db_session.commit()
                except Exception as e:
                    logger.error("Audit log DB persistence failed: %s", e)

            logger.info(f"Audit: {event} by {actor} on {resource} [{classification}]")
            return entry

    def _compute_hash(self, entry: Dict) -> str:
        raw = json.dumps(entry, sort_keys=True, ensure_ascii=False).encode()
        return hashlib.sha256(raw).hexdigest()

    def verify_chain(self, entries: list) -> bool:
        prev = None
        for entry in entries:
            expected_prev = prev or "0" * 64
            if entry["previous_hash"] != expected_prev:
                return False
            computed = self._compute_hash(
                {k: v for k, v in entry.items() if k != "hash"}
            )
            if entry["hash"] != computed:
                return False
            prev = entry["hash"]
        return True


audit_chain = AuditChain()


def iso_utc(dt) -> str:
    """Serializa un datetime como ISO-8601 UTC.

    SQLite devuelve datetimes sin tzinfo; se asume UTC para que la
    reconstrucción del hash coincida exactamente con la entrada original.
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()
