"""
Space Domain Awareness API v2.
Conciencia del dominio espacial: satélites, ASAT, SSA.
"""
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import time
import uuid

import httpx
from pydantic import BaseModel, Field

from app.db.session import async_session_factory
from app.db.models.persistence import EventStore
from app.core.config import settings
from app.core.security import require_clearance

router = APIRouter()


async def get_db():
    async with async_session_factory() as session:
        yield session


_tle_cache: Dict[str, Any] = {"fetched_at": 0.0, "tles": []}


def _parse_tle_epoch(line1: str) -> str:
    year = int(line1[18:20])
    day = float(line1[20:32])
    full_year = 2000 + year if year < 57 else 1900 + year
    dt = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day - 1)
    return dt.isoformat()


def _orbit_type(mean_motion: float, eccentricity: float) -> str:
    if eccentricity > 0.25:
        return "HEO"
    if mean_motion >= 11.25:
        return "LEO"
    if 0.9 <= mean_motion <= 1.1:
        return "GEO"
    return "MEO"


def _parse_tle_block(name: str, line1: str, line2: str) -> Dict[str, Any]:
    eccentricity = float("0." + line2[26:33].strip())
    mean_motion = float(line2[52:63])
    return {
        "name": name.strip(),
        "norad_id": line1[2:7].strip(),
        "intl_designator": line1[9:17].strip(),
        "epoch": _parse_tle_epoch(line1),
        "orbit_type": _orbit_type(mean_motion, eccentricity),
        "inclination_deg": float(line2[8:16]),
        "raan_deg": float(line2[17:25]),
        "eccentricity": eccentricity,
        "arg_perigee_deg": float(line2[34:42]),
        "mean_anomaly_deg": float(line2[43:51]),
        "mean_motion_rev_day": mean_motion,
        "tle_line1": line1,
        "tle_line2": line2,
    }


async def _fetch_tles() -> List[Dict[str, Any]]:
    now = time.monotonic()
    if _tle_cache["tles"] and (now - _tle_cache["fetched_at"]) < settings.CELESTRAK_CACHE_TTL:
        return _tle_cache["tles"]

    try:
        async with httpx.AsyncClient(timeout=settings.CELESTRAK_TIMEOUT) as client:
            response = await client.get(settings.CELESTRAK_TLE_URL, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Timeout contactando CelesTrak ({settings.CELESTRAK_TIMEOUT}s)",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error de red con CelesTrak: {exc}",
        ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CelesTrak respondio HTTP {response.status_code}",
        )

    lines = [ln.rstrip() for ln in response.text.splitlines() if ln.strip()]
    tles: List[Dict[str, Any]] = []
    i = 0
    try:
        while i + 2 < len(lines):
            name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
            if not (line1.startswith("1 ") and line2.startswith("2 ")):
                i += 1
                continue
            tles.append(_parse_tle_block(name, line1, line2))
            i += 3
    except (ValueError, IndexError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Catalogo TLE no parseable: {exc}",
        ) from exc

    if not tles:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CelesTrak no devolvio TLEs validos",
        )

    _tle_cache["tles"] = tles
    _tle_cache["fetched_at"] = now
    return tles


class AnomalyType(str, Enum):
    DEORBIT = "DEORBIT"
    SIGNAL_LOSS = "SIGNAL_LOSS"
    MANEUVER = "MANEUVER"
    ASAT_THREAT = "ASAT_THREAT"


class SatelliteAnomalyIn(BaseModel):
    satellite_id: str = Field(..., max_length=64)
    anomaly_type: AnomalyType
    details: Optional[str] = Field(None, max_length=2000)
    classification: str = Field("TOP_SECRET", max_length=32, pattern=r"^(OPEN|RESTRICTED|CONFIDENTIAL|SECRET|TOP_SECRET)$")


class ASATResponseType(str, Enum):
    HARD_KILL = "HARD_KILL"
    SOFT_KILL = "SOFT_KILL"
    EW_COUNTER = "EW_COUNTER"


class ASATResponseIn(BaseModel):
    threat_id: str = Field(..., max_length=64)
    response_type: ASATResponseType
    classification: str = Field("TOP_SECRET", max_length=32, pattern=r"^(OPEN|RESTRICTED|CONFIDENTIAL|SECRET|TOP_SECRET)$")


@router.get("/satellites/tracking", tags=["Space / Satellites"])
async def get_satellite_tracking(
    classification: str = "SECRET",
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("SECRET")),
):
    """Obtiene el catalogo TLE real desde CelesTrak (grupo configurable).

    Devuelve TLE crudo + epoca y elementos orbitales parseados. La propagacion
    de posicion requiere la libreria sgp4 (no instalada); mientras tanto se
    entregan los elementos orbitales para propagacion en cliente.
    """
    tles = await _fetch_tles()
    return {
        "satellites": tles,
        "total_tracked": len(tles),
        "source": "celestrak",
        "catalog_url": settings.CELESTRAK_TLE_URL,
        "propagation": "tle_only_sgp4_not_installed",
        "classification": classification,
    }


@router.post("/satellites/anomaly", tags=["Space / Anomalies"])
async def report_satellite_anomaly(
    payload: SatelliteAnomalyIn,
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("SECRET")),
):
    """Reporte de anomalía satelital."""
    event_id = str(uuid.uuid4())

    event = EventStore(
        aggregate_id=event_id,
        aggregate_type="SatelliteAnomaly",
        event_type="SATELLITE_ANOMALY",
        payload={
            "satellite_id": payload.satellite_id,
            "anomaly_type": payload.anomaly_type.value,
            "details": payload.details
        },
        actor="space_operator"
    )
    db.add(event)

    await db.commit()
    return {
        "event_id": event_id,
        "status": "anomaly_recorded",
        "response": "ANALYZING" if payload.anomaly_type != AnomalyType.ASAT_THREAT else "DEFENSIVE_MEASURES_ACTIVE",
        "classification": payload.classification
    }


@router.get("/space-situational-awareness", tags=["Space / SSA"])
async def get_ssa_status(
    classification: str = "SECRET",
    principal: dict = Depends(require_clearance("SECRET")),
):
    """Estado de Space Situational Awareness (SSA)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="SSA no configurado: no hay fuente de clima espacial ni catalogo de debris integrada",
    )


@router.post("/asat-response", tags=["Space / ASAT"])
async def initiate_asat_response(
    payload: ASATResponseIn,
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("SECRET")),
):
    """Inicia respuesta ante amenaza ASAT (Anti-Satellite)."""
    response_id = str(uuid.uuid4())

    event = EventStore(
        aggregate_id=response_id,
        aggregate_type="ASATResponse",
        event_type="ASAT_RESPONSE_INITIATED",
        payload={
            "threat_id": payload.threat_id,
            "response_type": payload.response_type.value,
            "authorization": "REQUIRED"
        },
        actor="space_command"
    )
    db.add(event)

    await db.commit()
    return {
        "response_id": response_id,
        "status": "awaiting_authorization",
        "response_type": payload.response_type.value,
        "classification": payload.classification
    }
