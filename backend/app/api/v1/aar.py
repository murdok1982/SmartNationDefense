# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.aar.service import aar_service

router = APIRouter()


class CreateAARRequest(BaseModel):
    operation_id: str
    operation_name: str
    start_time: str
    end_time: str = None
    participants: List[str] = []
    objectives: List[Dict[str, Any]] = []
    classification: str = "CONFIDENTIAL"
    created_by: str = "SYSTEM"


class TimelineEventRequest(BaseModel):
    timestamp: str
    event_type: str = "ACTION"
    description: str
    actor: str = ""
    location: Dict[str, Any] = {}
    outcome: str = ""
    significance: str = "NORMAL"


class LessonLearnedRequest(BaseModel):
    category: str = "TACTICAL"
    observation: str
    discussion: str = ""
    recommendation: str = ""
    priority: str = "MEDIUM"
    sustains: bool = True
    improves: bool = False


class FinalizeRequest(BaseModel):
    end_time: str = None
    outcomes: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    performance_metrics: Dict[str, Any] = {}


@router.post("/create")
async def create_aar(request: CreateAARRequest):
    return await aar_service.create_aar(request.model_dump())


@router.get("/{aar_id}")
async def get_aar(aar_id: str):
    aar = await aar_service.get_aar(aar_id)
    if not aar:
        raise HTTPException(status_code=404, detail="AAR no encontrada")
    return aar


@router.post("/{aar_id}/timeline")
async def add_timeline_event(aar_id: str, request: TimelineEventRequest):
    try:
        return await aar_service.add_timeline_event(aar_id, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{aar_id}/lessons")
async def add_lesson_learned(aar_id: str, request: LessonLearnedRequest):
    try:
        return await aar_service.add_lesson_learned(aar_id, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{aar_id}/replay")
async def get_replay(aar_id: str):
    try:
        return await aar_service.get_replay(aar_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{aar_id}/finalize")
async def finalize_aar(aar_id: str, request: FinalizeRequest):
    try:
        return await aar_service.finalize_aar(aar_id, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
