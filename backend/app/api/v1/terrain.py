# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.terrain.service import terrain_service
from app.services.terrain.elevation import ElevationProviderError
from app.core.security import require_clearance

router = APIRouter()


class LOSRequest(BaseModel):
    observer: Dict[str, float]
    target: Dict[str, float]
    observer_height_m: float = 2.0
    target_height_m: float = 2.0


class RouteAnalysisRequest(BaseModel):
    start: Dict[str, float]
    end: Dict[str, float]
    vehicle_type: str = "INFANTRY"
    avoid_obstacles: bool = True


class TerrainAnalysisRequest(BaseModel):
    center_lat: float
    center_lon: float
    radius_km: float = 10.0


class ElevationRequest(BaseModel):
    lat: float
    lon: float


class ObstacleDetectionRequest(BaseModel):
    center_lat: float
    center_lon: float
    radius_km: float = 10.0


def _raise_if_dem_error(exc: Exception) -> None:
    if isinstance(exc, ElevationProviderError):
        raise HTTPException(status_code=503, detail=f"Servicio DEM no disponible: {exc.detail}")
    raise exc


@router.post("/line-of-sight")
async def line_of_sight(
    request: LOSRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await terrain_service.line_of_sight(
            observer=request.observer,
            target=request.target,
            observer_height_m=request.observer_height_m,
            target_height_m=request.target_height_m,
        )
    except Exception as exc:
        _raise_if_dem_error(exc)


@router.post("/route-analysis")
async def route_analysis(
    request: RouteAnalysisRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await terrain_service.route_analysis(
            start=request.start,
            end=request.end,
            vehicle_type=request.vehicle_type,
            avoid_obstacles=request.avoid_obstacles,
        )
    except Exception as exc:
        _raise_if_dem_error(exc)


@router.post("/terrain-analysis")
async def terrain_analysis(
    request: TerrainAnalysisRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    area = {
        "center_lat": request.center_lat,
        "center_lon": request.center_lon,
        "radius_km": request.radius_km,
    }
    try:
        return await terrain_service.terrain_analysis(area=area)
    except Exception as exc:
        _raise_if_dem_error(exc)


@router.get("/elevation")
async def get_elevation(
    lat: float,
    lon: float,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await terrain_service.get_elevation(lat=lat, lon=lon)
    except Exception as exc:
        _raise_if_dem_error(exc)


@router.post("/obstacle-detection")
async def detect_obstacles(
    request: ObstacleDetectionRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    area = {
        "center_lat": request.center_lat,
        "center_lon": request.center_lon,
        "radius_km": request.radius_km,
    }
    try:
        return await terrain_service.detect_obstacles(area=area)
    except Exception as exc:
        _raise_if_dem_error(exc)
