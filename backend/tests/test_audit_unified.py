"""TASK-016 / TASK-027 — Auditoría unificada y persistente.

Verifica que la cadena de auditoría se persiste en la tabla canónica
``audit_log`` y que ``/audit/verify`` reconstruye y valida los hashes.
"""
from sqlalchemy import select

from app.core.audit import AuditChain, iso_utc
from app.db.models.persistence import AuditLog


def _rebuild(rows):
    return [
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


async def test_audit_chain_persists_canonical_row(db_session):
    chain = AuditChain()
    await chain.record(
        event="LOGIN",
        actor="u1",
        resource="user:u1",
        details={"ip": "203.0.113.7", "success": True, "username": "alice"},
        db_session=db_session,
    )

    rows = (await db_session.execute(select(AuditLog))).scalars().all()
    assert len(rows) == 1
    row = rows[0]
    assert row.actor == "u1"
    assert row.user_id == "u1"
    assert row.ip_address == "203.0.113.7"
    assert row.success is True
    assert row.row_hash
    assert row.timestamp is not None


async def test_audit_chain_verifies_and_detects_tampering(db_session):
    chain = AuditChain()
    for idx in range(3):
        await chain.record(
            event="TEST",
            actor="u1",
            resource=f"resource:{idx}",
            details={"success": True},
            db_session=db_session,
        )

    rows = (await db_session.execute(select(AuditLog).order_by(AuditLog.id.asc()))).scalars().all()
    entries = _rebuild(rows)
    assert chain.verify_chain(entries) is True

    # Manipulación: alterar el contexto de una fila invalida su hash
    entries[1]["details"] = {"tampered": True}
    assert chain.verify_chain(entries) is False


async def test_audit_persisted_columns_support_osint_api_filters(db_session):
    chain = AuditChain()
    await chain.record(
        event="LOGIN",
        actor="u2",
        resource="user:u2",
        details={"ip": "198.51.100.9", "success": False, "error": "Invalid credentials"},
        db_session=db_session,
    )

    failed = (
        await db_session.execute(select(AuditLog).where(AuditLog.success.is_(False)))
    ).scalars().all()
    assert len(failed) == 1
    assert failed[0].error_message == "Invalid credentials"
    assert failed[0].user_id == "u2"
