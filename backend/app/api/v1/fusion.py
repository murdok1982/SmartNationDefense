# -*- coding: utf-8 -*-
from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from pydantic import BaseModel

from app.services.fusion.jdl_fusion import jdl_fusion_engine
from app.core.security import require_clearance

router = APIRouter()


class ThreatAssessmentRequest(BaseModel):
    events: List[Dict[str, Any]]


class RelationshipRequest(BaseModel):
    entities: List[Dict[str, Any]]


class IntentionRequest(BaseModel):
    enemy_units: List[Dict[str, Any]]


class CTPRequest(BaseModel):
    events: List[Dict[str, Any]]


@router.post("/assess-threats")
async def assess_threats(
    request: ThreatAssessmentRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    result = await jdl_fusion_engine.assess_threats(request.events)
    return {
        "threat_level": result.threat_level,
        "hostile_units": [
            {
                "id": h.id,
                "unit_type": h.unit_type,
                "location": {"lat": h.location.lat, "lon": h.location.lon},
                "strength": h.strength,
                "threat_level": h.threat_level,
                "capability": h.capability,
                "intention": h.intention,
            }
            for h in result.hostile_units
        ],
        "friendly_units": [
            {
                "id": f.id,
                "unit_type": f.unit_type,
                "location": {"lat": f.location.lat, "lon": f.location.lon},
                "status": f.status,
                "strength": f.strength,
            }
            for f in result.friendly_units
        ],
        "neutral_entities": [
            {
                "id": n.id,
                "entity_type": n.entity_type,
                "location": {"lat": n.location.lat, "lon": n.location.lon},
                "description": n.description,
            }
            for n in result.neutral_entities
        ],
        "threat_zones": [
            {
                "zone_id": z.zone_id,
                "center": {"lat": z.center.lat, "lon": z.center.lon},
                "radius_km": z.radius_km,
                "threat_level": z.threat_level,
                "zone_type": z.zone_type,
                "description": z.description,
            }
            for z in result.threat_zones
        ],
        "recommended_actions": [
            {
                "action_type": a.action_type,
                "priority": a.priority,
                "description": a.description,
            }
            for a in result.recommended_actions
        ],
        "timestamp": result.timestamp,
        "assessment_id": result.assessment_id,
    }


@router.post("/relationships")
async def identify_relationships(
    request: RelationshipRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    result = await jdl_fusion_engine.identify_relationships(request.entities)
    return {
        "nodes": [
            {
                "id": n.id,
                "entity_type": n.entity_type,
                "location": {"lat": n.location.lat, "lon": n.location.lon},
                "source": n.source,
                "confidence": n.confidence,
            }
            for n in result.nodes
        ],
        "edges": [
            {
                "source_id": e.source_id,
                "target_id": e.target_id,
                "relationship_type": e.relationship_type,
                "strength": e.strength,
                "metadata": e.metadata,
            }
            for e in result.edges
        ],
    }


@router.post("/intentions")
async def evaluate_intentions(
    request: IntentionRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    results = await jdl_fusion_engine.evaluate_intentions(request.enemy_units)
    return [
        {
            "unit_id": r.unit_id,
            "predicted_intention": r.predicted_intention,
            "confidence": r.confidence,
            "indicators": r.indicators,
            "course_of_action": r.course_of_action,
        }
        for r in results
    ]


@router.post("/ctp")
async def generate_ctp(
    request: CTPRequest,
    principal: dict = Depends(require_clearance("RESTRICTED")),
):
    result = await jdl_fusion_engine.generate_ctp(request.events)
    return {
        "generated_at": result.generated_at,
        "version": result.version,
        "overall_threat_level": result.assessment.threat_level,
        "total_hostiles": len(result.assessment.hostile_units),
        "total_friendlies": len(result.assessment.friendly_units),
        "total_relationships": len(result.relationships.edges),
        "intentions_analyzed": len(result.intentions),
    }
