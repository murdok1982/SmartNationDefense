# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from app.services.reports.service import reports_service

router = APIRouter()


class SITREPRequest(BaseModel):
    classification: str = "CONFIDENTIAL"
    from_unit: str = ""
    to_unit: str = ""
    reference: str = ""
    enemy_forces: str = ""
    friendly_forces: str = ""
    attachments: str = ""
    weather_current: str = ""
    weather_forecast_12h: str = ""
    weather_forecast_24h: str = ""
    operations_ongoing: List[str] = []
    operations_completed: List[str] = []
    operations_planned: List[str] = []
    supply_status: str = ""
    critical_needs: List[str] = []
    personnel_strength: str = ""
    casualties: str = ""
    morale: str = ""
    comms_status: str = ""
    frequency_changes: str = ""
    distribution_list: List[str] = []
    created_by: str = "SYSTEM"
    operation_id: Optional[str] = None


class SPOTREPRequest(BaseModel):
    classification: str = "CONFIDENTIAL"
    size: str = ""
    activity: str = ""
    location: Dict[str, Any] = {}
    unit_identified: str = ""
    time_observed: Optional[str] = None
    equipment: str = ""
    narrative: str = ""
    assessment: str = ""
    distribution_list: List[str] = []
    created_by: str = "SYSTEM"


class SALUTERequest(BaseModel):
    classification: str = "CONFIDENTIAL"
    size: str = ""
    activity: str = ""
    location: Dict[str, Any] = {}
    unit: str = ""
    time: Optional[str] = None
    equipment: str = ""
    assessment: str = ""
    source_reliability: str = "B"
    info_credibility: str = "2"
    distribution_list: List[str] = []
    created_by: str = "SYSTEM"


class MEDEVACReportRequest(BaseModel):
    urgency: str = "ROUTINE"
    pickup_location: Dict[str, Any] = {}
    radio_freq: str = ""
    casualty_count: int = 0
    urgent_count: int = 0
    priority_count: int = 0
    routine_count: int = 0
    security: str = "N"
    evac_type: str = "MEDEVAC"
    equipment: List[str] = []
    casualty_status: str = ""
    special_equipment: str = ""
    terrain: str = ""
    requesting_unit: str = ""
    commander_name: str = ""
    distribution_list: List[str] = []
    created_by: str = "SYSTEM"


@router.post("/sitrep")
async def generate_sitrep(request: SITREPRequest):
    return await reports_service.generate_sitrep(request.model_dump())


@router.post("/spotrep")
async def generate_spotrep(request: SPOTREPRequest):
    return await reports_service.generate_spotrep(request.model_dump())


@router.post("/salute")
async def generate_salute(request: SALUTERequest):
    return await reports_service.generate_salute(request.model_dump())


@router.post("/medevac")
async def generate_medevac_report(request: MEDEVACReportRequest):
    return await reports_service.generate_medevac_report(request.model_dump())


@router.get("/{report_id}")
async def get_report(report_id: str):
    report = await reports_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return report


@router.get("")
async def list_reports(
    report_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await reports_service.list_reports(
        report_type=report_type,
        limit=limit,
        offset=offset,
    )
