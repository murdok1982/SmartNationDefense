# -*- coding: utf-8 -*-
import datetime
import logging
import os
import uuid

logger = logging.getLogger(__name__)


async def init_db(settings):
    """Siembra idempotente del usuario admin inicial.

    No crea tablas: el esquema lo gestionan exclusivamente las migraciones
    Alembic. Requiere ADMIN_INITIAL_PASSWORD en el entorno para el primer
    arranque; si no esta definida y no existe el admin, falla con error claro.
    """
    from sqlalchemy import select
    from app.db.session import async_session
    from app.db.models.persistence import User

    async with async_session() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        admin = result.scalars().first()
        if admin:
            logger.info("Usuario admin ya existe")
            return

        admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")
        if not admin_password:
            raise RuntimeError(
                "ADMIN_INITIAL_PASSWORD no definido: imposible crear el usuario "
                "admin inicial de forma segura. Configure la variable de entorno "
                "y reinicie el servicio."
            )

        from app.core.security import hash_password
        new_admin = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@sesis.mil",
            hashed_password=hash_password(admin_password),
            role="admin",
            classification_level="TOP_SECRET",
            is_active=True,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        session.add(new_admin)
        await session.commit()
        logger.info("Usuario admin creado por defecto (credencial tomada del entorno)")

    logger.info(f"Database initialized for environment: {settings.ENVIRONMENT}")
