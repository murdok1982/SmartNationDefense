# -*- coding: utf-8 -*-
import asyncio
import logging
import datetime

logger = logging.getLogger(__name__)


def _init_sync(settings):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_init_async(settings))
    finally:
        loop.close()


async def _init_async(settings):
    from app.db.session import engine
    from app.db.models.persistence import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas creadas/verificadas correctamente")
    except Exception as e:
        logger.error(f"Error creando tablas: {e}")
        return

    try:
        from app.db.session import async_session
        from app.db.models.persistence import User
        from sqlalchemy import select

        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == "admin"))
            admin = result.scalars().first()
            if not admin:
                import os
                admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")
                if not admin_password:
                    import secrets
                    admin_password = secrets.token_urlsafe(16)
                    logger.warning(
                        "ADMIN_INITIAL_PASSWORD no configurado. Password generada: %s "
                        "— CAMBIAR INMEDIATAMENTE tras primer acceso.",
                        admin_password,
                    )
                from app.core.security import hash_password
                import uuid
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
                logger.info("Usuario admin creado por defecto")
            else:
                logger.info("Usuario admin ya existe")
    except Exception as e:
        logger.error(f"Error creando usuario admin: {e}")

    logger.info(f"Database initialized for environment: {settings.ENVIRONMENT}")


def init_db(settings):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(_init_sync, settings).result(timeout=30)
    else:
        _init_sync(settings)
