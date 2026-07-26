# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
from pydantic import BaseModel

from app.db.session import async_session_factory
from app.services.prediction.threat_prediction import threat_prediction_service

router = APIRouter()


async def get_db():
    async with async_session_factory() as session:
        yield session


class PredictMovementRequest(BaseModel):
    id: str
    lat: float
    lon: float
    speed: float = 0.0
    heading: float = 0.0
    threat_level: float = 50.0
    time_horizon_min: int = 60


class AnomalyDetectionRequest(BaseModel):
    events: List[Dict[str, Any]]


class PatternOfLifeRequest(BaseModel):
    unit_id: str


class EarlyWarningRequest(BaseModel):
    friendly_locations: List[Dict[str, float]]
    threat_radius_km: float = 50.0


@router.post("/predict-movement")
async def predict_movement(request: PredictMovementRequest):
    return await threat_prediction_service.predict_movement(
        unit_data=request.model_dump(),
        time_horizon_min=request.time_horizon_min,
    )


@router.post("/detect-anomalies")
async def detect_anomalies(request: AnomalyDetectionRequest):
    return await threat_prediction_service.detect_anomalies(request.events)


@router.post("/pattern-of-life")
async def analyze_pattern_of_life(request: PatternOfLifeRequest):
    return await threat_prediction_service.analyze_pattern_of_life(request.unit_id)


@router.post("/early-warning")
async def early_warning(request: EarlyWarningRequest):
    return await threat_prediction_service.early_warning(
        friendly_locations=request.friendly_locations,
        threat_radius_km=request.threat_radius_km,
    )


@router.get("/threat-trend")
async def threat_trend(
    window_hours: int = 24,
    buckets: int = 6,
    db: AsyncSession = Depends(get_db),
):
    if not (1 <= window_hours <= 24 * 30):
        raise HTTPException(status_code=400, detail="window_hours fuera de rango (1-720)")
    if not (2 <= buckets <= 48):
        raise HTTPException(status_code=400, detail="buckets fuera de rango (2-48)")
    try:
        return await threat_prediction_service.statistical_threat_trend(
            db=db,
            window_hours=window_hours,
            buckets=buckets,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No se pudieron calcular estadisticas desde la base de datos: {exc}",
        ) from exc
