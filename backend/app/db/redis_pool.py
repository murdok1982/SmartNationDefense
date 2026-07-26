# -*- coding: utf-8 -*-
import logging

import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)

_pool = None


def get_redis_client():
    global _pool
    if _pool is None:
        try:
            _pool = redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as exc:
            logger.warning("redis_pool: no se pudo conectar a Redis (%s)", exc)
            _pool = None
    return _pool


async def get_redis_pool():
    client = get_redis_client()
    if client is None:
        return None
    try:
        await client.ping()
    except Exception as exc:
        logger.warning("redis_pool: Redis no responde (%s)", exc)
        return None
    return client
