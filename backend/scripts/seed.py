import asyncio
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed")


async def seed():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from app.db.init_db import init_db
    from app.core.config import get_settings

    settings = get_settings()
    logger.info("Iniciando seed de datos...")

    await init_db(settings)

    # Seed adicional de ejemplo para la demo
    from sqlalchemy import select
    from app.db.session import async_session
    from app.db.models.persistence import User

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.username == "analyst")
        )
        if not result.scalars().first():
            from app.core.security import hash_password
            import uuid
            import datetime

            analyst = User(
                id=str(uuid.uuid4()),
                username="analyst",
                email="analyst@sesis.mil",
                hashed_password=hash_password("analyst123"),
                role="analyst",
                classification_level="SECRET",
                is_active=True,
                created_at=datetime.datetime.now(datetime.timezone.utc),
            )
            session.add(analyst)
            await session.commit()
            logger.info("Usuario 'analyst' creado (password: analyst123)")

    logger.info("Seed completado exitosamente.")


async def main():
    try:
        await seed()
    except Exception as e:
        logger.error("Seed fallo: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
