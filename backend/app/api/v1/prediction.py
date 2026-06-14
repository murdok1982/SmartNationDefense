# -*- coding: utf-8 -*-
from fastapi import APIRouter
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.prediction.threat_prediction import threat_prediction_service

router = APIRouter()


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
