"""
Border & Maritime Control API v2.
Control fronterizo, ADIZ (Air Defense ID Zone), dominio marítimo.
"""
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import asyncio
import json
import uuid

from pydantic import BaseModel, Field

from app.db.session import async_session_factory
from app.db.models.persistence import EventStore, Asset, Sensor
from app.core.config import settings
from app.core.events import event_bus
from app.core.security import require_clearance

router = APIRouter()


async def get_db():
    async with async_session_factory() as session:
        yield session


class PerimeterEventType(str, Enum):
    INTRUSION = "INTRUSION"
    MOVEMENT = "MOVEMENT"
    BREACH = "BREACH"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PerimeterSensorIn(BaseModel):
    sensor_id: str = Field(..., max_length=64)
    event_type: PerimeterEventType
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    severity: Severity = Severity.MEDIUM
    classification: str = Field("CONFIDENTIAL", max_length=32, pattern=r"^(OPEN|RESTRICTED|CONFIDENTIAL|SECRET|TOP_SECRET)$")


class ADIZIn(BaseModel):
    aircraft_id: str = Field(..., max_length=64)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    altitude: float
    speed: float = Field(..., ge=0.0)
    heading: float = Field(..., ge=0.0, le=360.0)
    classification: str = Field("SECRET", max_length=32, pattern=r"^(OPEN|RESTRICTED|CONFIDENTIAL|SECRET|TOP_SECRET)$")


class InterdictionIn(BaseModel):
    vessel_mmsi: str = Field(..., max_length=32, pattern=r"^[0-9]+$")
    reason: str = Field(..., max_length=64, pattern=r"^[A-Z_]+$")
    classification: str = Field("SECRET", max_length=32, pattern=r"^(OPEN|RESTRICTED|CONFIDENTIAL|SECRET|TOP_SECRET)$")


@router.post("/perimeter-sensor", tags=["Border / Sensors"])
async def report_perimeter_event(
    payload: PerimeterSensorIn,
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("CONFIDENTIAL")),
):
    """Reporte de sensor perimetral fronterizo."""
    event_id = str(uuid.uuid4())
    event = EventStore(
        aggregate_id=event_id,
        aggregate_type="BorderSensor",
        event_type="PERIMETER_ALERT",
        payload={
            "sensor_id": payload.sensor_id,
            "event_type": payload.event_type.value,
            "position": f"{payload.lat},{payload.lon}",
            "severity": payload.severity.value
        }
    )
    db.add(event)

    await db.commit()
    return {"event_id": event_id, "status": "recorded", "classification": payload.classification}


@router.get("/perimeter-status", tags=["Border / Status"])
async def get_perimeter_status(
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("CONFIDENTIAL")),
):
    """Estado del perímetro fronterizo calculado desde sensores y alertas en BD."""
    sensors = (await db.execute(select(Sensor))).scalars().all()
    if not sensors:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Perimetro no configurado: no hay sensores registrados en la base de datos",
        )

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    alert_rows = (
        await db.execute(
            select(EventStore).where(
                EventStore.event_type == "PERIMETER_ALERT",
                EventStore.occurred_at >= since,
            )
        )
    ).scalars().all()

    sensor_sector: Dict[str, str] = {}
    sectors: Dict[str, Dict[str, Any]] = {}
    active_total = 0
    for sensor in sensors:
        sector = (sensor.metadata_json or {}).get("sector", "SIN_SECTOR")
        sensor_sector[sensor.id] = sector
        bucket = sectors.setdefault(sector, {"name": sector, "sensors_active": 0, "sensors_total": 0, "alerts_24h": 0})
        bucket["sensors_total"] += 1
        if (sensor.status or "").upper() == "ACTIVE":
            bucket["sensors_active"] += 1
            active_total += 1

    for alert in alert_rows:
        sector = sensor_sector.get((alert.payload or {}).get("sensor_id", ""), "SIN_SECTOR")
        if sector in sectors:
            sectors[sector]["alerts_24h"] += 1

    for bucket in sectors.values():
        bucket["status"] = "SECURE" if bucket["alerts_24h"] == 0 else ("ELEVATED" if bucket["alerts_24h"] < 5 else "ALERT")

    return {
        "sectors": list(sectors.values()),
        "total_sensors": len(sensors),
        "active_sensors": active_total,
        "alerts_last_24h": len(alert_rows),
        "source": "database",
    }


@router.post("/adiz-violation", tags=["Border / ADIZ"])
async def report_adiz_violation(
    payload: ADIZIn,
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("CONFIDENTIAL")),
):
    """Reporte de violación de ADIZ (Air Defense Identification Zone)."""
    event_id = str(uuid.uuid4())

    event = EventStore(
        aggregate_id=event_id,
        aggregate_type="ADIZ",
        event_type="ADIZ_VIOLATION",
        payload={
            "aircraft_id": payload.aircraft_id,
            "position": f"{payload.lat},{payload.lon},{payload.altitude}",
            "speed": payload.speed,
            "heading": payload.heading,
            "violation_type": "UNAUTHORIZED_ENTRY"
        }
    )
    db.add(event)

    await db.commit()
    await event_bus.publish("border.adiz.violation", {
        "event_id": event_id,
        "aircraft_id": payload.aircraft_id,
        "lat": payload.lat,
        "lon": payload.lon,
        "altitude": payload.altitude,
        "speed": payload.speed,
        "heading": payload.heading,
        "classification": payload.classification,
    })
    return {
        "event_id": event_id,
        "status": "violation_recorded",
        "order_event_subject": "border.adiz.violation",
        "classification": payload.classification
    }


@router.get("/maritime-tracks", tags=["Maritime / AIS"])
async def get_maritime_tracks(
    zone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("CONFIDENTIAL")),
):
    """Obtiene tracks marítimos (AIS) en zona económica exclusiva."""
    if not settings.AISSTREAM_API_KEY:
        return {
            "zone": zone or "EEZ_COMPLETE",
            "vessels": [],
            "total_tracks": 0,
            "alerts": 0,
            "source": "unconfigured",
        }

    if not settings.AISSTREAM_BOUNDING_BOXES:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="AISSTREAM_BOUNDING_BOXES no configurado",
        )

    try:
        import websockets
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Libreria 'websockets' no disponible para conectar con AISStream",
        ) from exc

    try:
        bounding_boxes = json.loads(settings.AISSTREAM_BOUNDING_BOXES)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AISSTREAM_BOUNDING_BOXES no es JSON valido",
        ) from exc

    vessels: List[Dict[str, Any]] = []
    seen_mmsi = set()
    deadline = settings.AISSTREAM_COLLECT_SECONDS
    try:
        async with websockets.connect(settings.AISSTREAM_URL, open_timeout=10) as ws:
            await ws.send(json.dumps({
                "APIKey": settings.AISSTREAM_API_KEY,
                "BoundingBoxes": bounding_boxes,
                "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
            }))
            while True:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=deadline)
                except asyncio.TimeoutError:
                    break
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if message.get("MessageType") != "PositionReport":
                    continue
                report = message.get("Message", {}).get("PositionReport", {})
                mmsi = str(report.get("UserID", ""))
                if not mmsi or mmsi in seen_mmsi:
                    continue
                seen_mmsi.add(mmsi)
                vessels.append({
                    "mmsi": mmsi,
                    "position": {"lat": report.get("Latitude"), "lon": report.get("Longitude")},
                    "speed_knots": report.get("Sog"),
                    "course_deg": report.get("Cog"),
                    "heading_deg": report.get("TrueHeading"),
                    "nav_status": report.get("NavigationalStatus"),
                })
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error conectando con AISStream: {exc}",
        ) from exc

    return {
        "zone": zone or "EEZ_COMPLETE",
        "vessels": vessels,
        "total_tracks": len(vessels),
        "alerts": 0,
        "source": "aisstream",
    }


@router.post("/maritime-interdiction", tags=["Maritime / Operations"])
async def initiate_maritime_interdiction(
    payload: InterdictionIn,
    db: AsyncSession = Depends(get_db),
    principal: dict = Depends(require_clearance("CONFIDENTIAL")),
):
    """Inicia interdicción marítima."""
    interdiction_id = str(uuid.uuid4())

    event = EventStore(
        aggregate_id=interdiction_id,
        aggregate_type="MaritimeInterdiction",
        event_type="INTERDICTION_STARTED",
        payload={
            "vessel_mmsi": payload.vessel_mmsi,
            "reason": payload.reason,
            "force_used": "MINIMAL"
        }
    )
    db.add(event)

    available_units = (
        await db.execute(
            select(Asset.id).where(
                Asset.kind.in_(["NAVAL", "COAST_GUARD", "PATROL"]),
                Asset.current_status == "active",
            )
        )
    ).scalars().all()

    await db.commit()
    await event_bus.publish("border.maritime.interdiction", {
        "interdiction_id": interdiction_id,
        "vessel_mmsi": payload.vessel_mmsi,
        "reason": payload.reason,
        "classification": payload.classification,
    })
    return {
        "interdiction_id": interdiction_id,
        "status": "order_recorded",
        "order_event_subject": "border.maritime.interdiction",
        "response_units": list(available_units),
        "classification": payload.classification
    }
