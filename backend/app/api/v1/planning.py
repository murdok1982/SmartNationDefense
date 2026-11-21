# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.planning.opord_enhanced import enhanced_opord_service
from app.core.security import require_clearance

router = APIRouter()


class CreateOPORDRequest(BaseModel):
    operation_name: str
    classification: str = "SECRET"
    paragraph_1_situation: Dict[str, Any] = {}
    paragraph_2_mission: Dict[str, Any] = {}
    paragraph_3_execution: Dict[str, Any] = {}
    paragraph_4_sustainment: Dict[str, Any] = {}
    paragraph_5_command_signal: Dict[str, Any] = {}
    annexes: List[Dict[str, Any]] = []
    created_by: str = "SYSTEM"
    parent_opord_id: str = None


class UpdateParagraphRequest(BaseModel):
    data: Dict[str, Any]


class AnnexRequest(BaseModel):
    annex_type: str
    title: str
    content: Dict[str, Any] = {}
    classification: str = "SECRET"


class COAComparisonRequest(BaseModel):
    coa_list: List[Dict[str, Any]]


@router.post("/create")
async def create_opord(
    request: CreateOPORDRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    return await enhanced_opord_service.create_opord(request.model_dump())


@router.get("/{opord_id}")
async def get_opord(
    opord_id: str,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    opord = await enhanced_opord_service.get_opord(opord_id)
    if not opord:
        raise HTTPException(status_code=404, detail="OPORD no encontrada")
    return opord


@router.put("/{opord_id}/paragraph/{paragraph}")
async def update_paragraph(
    opord_id: str,
    paragraph: str,
    request: UpdateParagraphRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.update_paragraph(opord_id, paragraph, request.data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{opord_id}/annex")
async def add_annex(
    opord_id: str,
    request: AnnexRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.add_annex(opord_id, request.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{opord_id}/approve")
async def approve_opord(
    opord_id: str,
    approver: str = "COMMANDER",
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.approve_opord(opord_id, approver)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{opord_id}/distribute")
async def distribute_opord(
    opord_id: str,
    distribution_list: List[str],
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.distribute_opord(opord_id, distribution_list)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{opord_id}/fragord")
async def generate_fragord(
    opord_id: str,
    changes: Dict[str, Any],
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.generate_fragord(opord_id, changes)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/coa-compare")
async def compare_coa(
    request: COAComparisonRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    return await enhanced_opord_service.compare_coa(request.coa_list)


@router.get("/{opord_id}/risk-assessment")
async def risk_assessment(
    opord_id: str,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.risk_assessment(opord_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{opord_id}/sync-matrix")
async def get_sync_matrix(
    opord_id: str,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.generate_sync_matrix(opord_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{opord_id}/validate")
async def validate_opord(
    opord_id: str,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    try:
        return await enhanced_opord_service.validate_opord(opord_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
