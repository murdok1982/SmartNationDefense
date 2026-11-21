from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from sqlalchemy import select, desc

from app.api.osint.deps import *
from app.core.audit import audit_chain, iso_utc
from app.db.models.persistence import AuditLog

router = APIRouter()


def _serialize(row: AuditLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id or row.actor,
        "username": row.username or "",
        "action": row.action,
        "resource_type": row.resource_type,
        "resource_id": row.resource_id,
        "ip_address": row.ip_address or "",
        "user_agent": row.user_agent or "",
        "request_id": row.request_id or "",
        "success": bool(row.success) if row.success is not None else True,
        "error_message": row.error_message or "",
        "details": row.details or row.context or {},
        "timestamp": iso_utc(row.ts) or None,
        "previous_hash": row.prev_hash,
        "hash": row.row_hash,
    }


@router.get("")
async def list_audit_log(
    db: DBSession,
    _admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    action: str | None = None,
    user_id: str | None = None,
    success: bool | None = None,
) -> list[dict[str, Any]]:
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action == action)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)
    if success is not None:
        q = q.where(AuditLog.success == success)
    q = q.order_by(desc(AuditLog.id)).offset(skip).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [_serialize(r) for r in rows]


@router.get("/chain")
async def list_audit_chain(
    db: DBSession,
    _admin: AdminUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> list[dict[str, Any]]:
    q = select(AuditLog).order_by(AuditLog.id.asc()).offset(skip).limit(limit)
    rows = (await db.execute(q)).scalars().all()
    return [
        {
            "index": r.id,
            "timestamp": r.ts.isoformat() if r.ts else None,
            "action": r.action,
            "user_id": r.user_id or r.actor,
            "resource": f"{r.resource_type}:{r.resource_id}",
            "details": r.details or r.context or {},
            "previous_hash": r.prev_hash,
            "hash": r.row_hash,
        }
        for r in rows
    ]


@router.get("/verify")
async def verify_chain_endpoint(
    db: DBSession,
    _admin: AdminUser,
) -> dict[str, Any]:
    """Recalcula cada hash de la cadena persistida y detecta manipulación.

    Devuelve ``{ok, total, broken_at, last_hash, reason?}``.
    """
    q = select(AuditLog).order_by(AuditLog.id.asc())
    rows = (await db.execute(q)).scalars().all()
    entries = [
        {
            "timestamp": iso_utc(r.ts),
            "event": r.action,
            "actor": r.actor,
            "resource": f"{r.resource_type}:{r.resource_id}",
            "classification": (r.context or {}).get("classification", "restricted"),
            "details": r.context or {},
            "previous_hash": r.prev_hash,
            "hash": r.row_hash,
        }
        for r in rows
    ]
    total = len(entries)
    if total == 0:
        return {"ok": True, "total": 0, "broken_at": None, "last_hash": None}

    ok = audit_chain.verify_chain(entries)
    if ok:
        return {"ok": True, "total": total, "broken_at": None, "last_hash": entries[-1]["hash"]}

    # Localizar el primer eslabón roto
    prev = "0" * 64
    for idx, entry in enumerate(entries):
        computed = audit_chain._compute_hash({k: v for k, v in entry.items() if k != "hash"})
        if entry["previous_hash"] != prev or entry["hash"] != computed:
            return {
                "ok": False,
                "total": total,
                "broken_at": idx,
                "last_hash": entries[-1]["hash"],
                "reason": "hash mismatch" if entry["previous_hash"] == prev else "previous_hash mismatch",
            }
        prev = entry["hash"]
    return {"ok": False, "total": total, "broken_at": None, "last_hash": entries[-1]["hash"]}
