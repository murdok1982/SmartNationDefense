# -*- coding: utf-8 -*-
from typing import List

from fastapi import APIRouter, HTTPException

from app.services.tactical.coa_engine import (
    coa_engine,
    MissionParams,
    CourseOfAction,
    RiskAssessment,
    WeaponAssessment,
    ComparisonCriteria,
    ScoredCOA,
)

router = APIRouter(prefix="/coa", tags=["COA v3"])


@router.post("/generate", response_model=List[CourseOfAction])
async def generate_coas(mission: MissionParams):
    """Genera múltiples Cursos de Acción usando algoritmos ROAD."""
    coas = await coa_engine.generate_coas(mission)
    if not coas:
        raise HTTPException(status_code=404, detail="No se pudieron generar COAs")
    return coas


@router.post("/assess-risk", response_model=RiskAssessment)
async def assess_risk(coa: CourseOfAction, mission: MissionParams):
    """Evalúa la matriz de riesgo probabilidad x impacto para un COA."""
    return await coa_engine.assess_risk(coa, mission)


@router.post("/weapon-availability", response_model=WeaponAssessment)
async def weapon_availability(coa: CourseOfAction):
    """Evalúa la disponibilidad de armamento y munición para un COA."""
    return await coa_engine.assess_weapon_availability(coa)


@router.post("/compare", response_model=List[ScoredCOA])
async def compare_coas(
    coas: List[CourseOfAction],
    criteria: ComparisonCriteria,
    mission: MissionParams,
):
    """Compara múltiples COAs usando weighted sum model y devuelve ranking."""
    ranked = await coa_engine.compare_coas(coas, criteria, mission)
    return ranked


@router.get("/templates", response_model=List[dict])
async def get_templates():
    """Devuelve las plantillas ROAD disponibles (ataque frontal, envolvimiento, etc.)."""
    return coa_engine.get_templates()
