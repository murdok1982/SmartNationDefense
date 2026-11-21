# -*- coding: utf-8 -*-
"""Re-export de Unified User (ADR-003).

``app/api/osint/auth.py`` e ``app/api/osint/deps.py`` importan
``User`` desde este módulo; ahora resuelve a
``app.db.models.persistence.User`` (Unified User, tabla ``users`` única).
"""
from app.db.models.persistence import User

__all__ = ["User"]
