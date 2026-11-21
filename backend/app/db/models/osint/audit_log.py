"""Modelo de auditoría — re-export del modelo canónico (TASK-016).

Históricamente existían tres tablas de auditoría en paralelo:
``audit_logs`` (osint), ``audit_chain`` (osint) y ``audit_log`` (persistence).
Desde TASK-016 sólo existe la tabla canónica ``audit_log`` definida en
``app.db.models.persistence``; este módulo mantiene el import histórico
funcionando sin duplicar el mapeo SQLAlchemy.
"""

from app.db.models.persistence import AuditLog

__all__ = ["AuditLog"]
