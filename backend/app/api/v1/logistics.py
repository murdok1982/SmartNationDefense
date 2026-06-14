# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.services.logistics.service import logistics_service

router = APIRouter()


class SupplyRequest(BaseModel):
    supply_type: str
    quantity: float
    unit: str
    delivery_location: Dict[str, Any]
    priority: str = "MEDIUM"
    justification: str = ""
    requested_by: str = "UNKNOWN"
    eta: Optional[str] = None


class DeliveryRequest(BaseModel):
    request_id: Optional[str] = None
    supply_type: str
    quantity_delivered: float
    delivered_by: str
    delivered_to: str
    location: Dict[str, Any]
    condition: str = "GOOD"


class MEDEVACRequest(BaseModel):
    casualty_id: str
    casualty_name: str = ""
    location: Dict[str, Any]
    urgency: str = "ROUTINE"
    type: str = "MEDEVAC"
    equipment: List[str] = []
    security: str = "N"
    marked: bool = False
    casualty_count: int = 1
    special_equipment: str = ""
    casualty_status: str = ""
    terrain_description: str = ""
    radio_freq: str = ""


class PersonnelRequest(BaseModel):
    name: str
    rank: str
    unit: str
    status: str = "ACTIVE"
    location: Dict[str, Any] = {}
    medical_status: str = "FIT"
    role: str = ""


class MaintenanceRequest(BaseModel):
    equipment_id: str
    equipment_type: str
    issue_type: str
    severity: str = "MEDIUM"
    description: str
    reported_by: str
    location: Dict[str, Any] = {}
    priority: str = "MEDIUM"
    estimated_repair_time_h: Optional[float] = None
    parts_needed: List[str] = []


@router.get("/supplies")
async def get_supplies(
    supply_type: Optional[str] = None,
    location_id: Optional[str] = None,
    status: Optional[str] = None,
):
    return await logistics_service.get_supplies(
        supply_type=supply_type,
        location_id=location_id,
        status=status,
    )


@router.post("/request")
async def request_supply(request: SupplyRequest):
    return await logistics_service.request_supply(request.model_dump())


@router.post("/delivery")
async def register_delivery(request: DeliveryRequest):
    return await logistics_service.register_delivery(request.model_dump())


@router.get("/status")
async def get_supply_status():
    return await logistics_service.get_supply_status()


@router.post("/medevac")
async def create_medevac(request: MEDEVACRequest):
    return await logistics_service.create_medevac(request.model_dump())


@router.get("/personnel")
async def get_personnel(
    unit_id: Optional[str] = None,
    status: Optional[str] = None,
):
    return await logistics_service.get_personnel_status(
        unit_id=unit_id,
        status_filter=status,
    )


@router.post("/maintenance")
async def report_maintenance(request: MaintenanceRequest):
    return await logistics_service.report_maintenance(request.model_dump())
