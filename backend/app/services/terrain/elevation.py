# -*- coding: utf-8 -*-
import logging
import time
from typing import Dict, List, Optional, Tuple

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100


class ElevationProviderError(Exception):
    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


_memory_cache: Dict[str, Tuple[float, float]] = {}


def _cache_key(lat: float, lon: float) -> str:
    return f"{lat:.5f}:{lon:.5f}"


async def _get_redis():
    try:
        from app.db.redis_pool import get_redis_pool
        return await get_redis_pool()
    except Exception:
        return None


def _memory_get(key: str) -> Optional[float]:
    entry = _memory_cache.get(key)
    if entry and entry[1] > time.monotonic():
        return entry[0]
    _memory_cache.pop(key, None)
    return None


async def fetch_elevations(points: List[Tuple[float, float]]) -> List[float]:
    if not points:
        return []

    ttl = settings.TERRAIN_ELEVATION_CACHE_TTL
    redis = await _get_redis()
    results: List[Optional[float]] = [None] * len(points)
    missing: List[int] = []

    for idx, (lat, lon) in enumerate(points):
        key = _cache_key(lat, lon)
        cached = _memory_get(key)
        if cached is None and redis is not None:
            try:
                raw = await redis.get(f"terrain:elev:{key}")
                if raw is not None:
                    cached = float(raw)
                    _memory_cache[key] = (cached, time.monotonic() + ttl)
            except Exception:
                cached = None
        if cached is None:
            missing.append(idx)
        else:
            results[idx] = cached

    if missing:
        await _fetch_missing(points, results, missing, redis, ttl)

    return [float(r) for r in results]


async def _fetch_missing(
    points: List[Tuple[float, float]],
    results: List[Optional[float]],
    missing: List[int],
    redis,
    ttl: int,
) -> None:
    now = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=settings.TERRAIN_ELEVATION_TIMEOUT) as client:
            for start in range(0, len(missing), _BATCH_SIZE):
                chunk = missing[start:start + _BATCH_SIZE]
                payload = {
                    "locations": [
                        {"latitude": points[i][0], "longitude": points[i][1]}
                        for i in chunk
                    ]
                }
                response = await client.post(settings.TERRAIN_ELEVATION_API_URL, json=payload)
                if response.status_code != 200:
                    raise ElevationProviderError(
                        f"Proveedor DEM respondio HTTP {response.status_code}"
                    )
                data = response.json()
                elevations = data.get("results")
                if not isinstance(elevations, list) or len(elevations) != len(chunk):
                    raise ElevationProviderError(
                        "Respuesta DEM invalida: numero de resultados no coincide"
                    )
                for i, item in zip(chunk, elevations):
                    elevation = item.get("elevation")
                    if elevation is None:
                        raise ElevationProviderError(
                            "Respuesta DEM invalida: elevacion ausente"
                        )
                    value = float(elevation)
                    results[i] = value
                    key = _cache_key(points[i][0], points[i][1])
                    _memory_cache[key] = (value, now + ttl)
                    if redis is not None:
                        try:
                            await redis.set(f"terrain:elev:{key}", str(value), ex=ttl)
                        except Exception:
                            pass
    except ElevationProviderError:
        raise
    except httpx.TimeoutException as exc:
        raise ElevationProviderError(
            f"Timeout contactando proveedor DEM ({settings.TERRAIN_ELEVATION_TIMEOUT}s)"
        ) from exc
    except httpx.HTTPError as exc:
        raise ElevationProviderError(f"Error de red con proveedor DEM: {exc}") from exc
    except (ValueError, KeyError, TypeError) as exc:
        raise ElevationProviderError(f"Respuesta DEM no parseable: {exc}") from exc
