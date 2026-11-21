# -*- coding: utf-8 -*-
"""Vocabulario Intel + Unified User (ADR-003).

El modelo ``User`` ahora vive en ``app.db.models.persistence``
(Unified User, tabla ``users`` única). Este módulo re-exporta el
modelo para que todos los imports existentes de
``from app.db.models.intel.user import User, RoleEnum`` sigan
funcionando, y define la ``RoleEnum`` del lado Intel.
"""
import enum

from app.db.models.persistence import User

__all__ = ["User", "RoleEnum"]


class RoleEnum(str, enum.Enum):
    """Roles de inteligencia (usuario / institucional / admin)."""

    user = "user"
    institutional = "institutional"
    admin = "admin"
