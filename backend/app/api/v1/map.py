# -*- coding: utf-8 -*-
from fastapi import APIRouter
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.mapping.tactical_map import tactical_map_service

router = APIRouter()


class OverlayRequest(BaseModel):
    name: str
    layer_type: str = "TACTICAL"
    geojson: Dict[str, Any] = {}
    style: Dict[str, Any] = {}
    visible: bool = True
    created_by: str = "SYSTEM"
    metadata: Dict[str, Any] = {}


class UnitTrackRequest(BaseModel):
    unit_id: str
    lat: float
    lon: float
    altitude: float = 0.0
    heading: float = 0.0
    speed: float = 0.0
    status: str = "ACTIVE"


class EngagementZoneRequest(BaseModel):
    unit_location: Dict[str, float]
    weapon_system: str = "INFANTRY"


class CommRangeRequest(BaseModel):
    transmitter_location: Dict[str, float]
    comm_system: str = "VHF"
    terrain_factor: float = 0.7


@router.get("/layers")
async def get_layers():
    return await tactical_map_service.get_layers()


@router.post("/overlay")
async def add_overlay(request: OverlayRequest):
    return await tactical_map_service.add_overlay(request.model_dump())


@router.get("/overlay")
async def get_overlays(layer_type: str = None):
    return await tactical_map_service.get_overlays(layer_type=layer_type)


@router.delete("/overlay/{overlay_id}")
async def remove_overlay(overlay_id: str):
    success = await tactical_map_service.remove_overlay(overlay_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Overlay no encontrado")
    return {"status": "removed", "overlay_id": overlay_id}


@router.post("/track")
async def track_unit(request: UnitTrackRequest):
    return await tactical_map_service.track_unit(request.model_dump())


@router.get("/unit/{unit_id}/history")
async def get_unit_history(
    unit_id: str,
    start_time: str = None,
    end_time: str = None,
    limit: int = 100,
):
    return await tactical_map_service.get_unit_history(
        unit_id=unit_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
    )


@router.post("/engagement-zone")
async def calculate_engagement_zone(request: EngagementZoneRequest):
    return await tactical_map_service.calculate_engagement_zone(
        unit_location=request.unit_location,
        weapon_system=request.weapon_system,
    )


@router.post("/comm-range")
async def calculate_comm_range(request: CommRangeRequest):
    return await tactical_map_service.calculate_comm_range(
        transmitter_location=request.transmitter_location,
        comm_system=request.comm_system,
        terrain_factor=request.terrain_factor,
    )


@router.get("/state")
async def get_map_state():
    return await tactical_map_service.get_map_state()
