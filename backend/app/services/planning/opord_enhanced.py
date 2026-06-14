# -*- coding: utf-8 -*-
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class EnhancedOPORDService:
    OPORD_TEMPLATE = {
        "paragraph_1_situation": {
            "enemy_forces": {
                "composition": "",
                "strength": "",
                "location": "",
                "capabilities": "",
                "likely_course_of_action": "",
            },
            "friendly_forces": {
                "higher_unit_mission": "",
                "adjacent_units": "",
                "attachments_detachments": "",
            },
            "civilian": {
                "population": "",
                "refugees": "",
                "infrastructure": "",
            },
            "terrain_weather": {
                "terrain_analysis": "",
                "weather": "",
            },
        },
        "paragraph_2_mission": {
            "who": "",
            "what": "",
            "when": "",
            "where": "",
            "why": "",
            "mission_statement": "",
        },
        "paragraph_3_execution": {
            "commander_intent": {
                "purpose": "",
                "key_tasks": "",
                "end_state": "",
            },
            "concept_of_operations": {
                "scheme_of_maneuver": "",
                "scheme_of_fires": "",
                "phases": [],
            },
            "tasks_to_subordinate_units": [],
            "coordinating_instructions": {
                "timeline": "",
                "rules_of_engagement": "",
                "fire_support_coordination": "",
                "airspace_control": "",
            },
        },
        "paragraph_4_sustainment": {
            "logistics": {
                "supply": "",
                "transportation": "",
                "maintenance": "",
            },
            "personnel": {
                "strength": "",
                "casualty_handling": "",
                "EPW_handling": "",
            },
            "medical": {
                "medical_facilities": "",
                "evacuation_plan": "",
                "blood_supply": "",
            },
        },
        "paragraph_5_command_signal": {
            "command": {
                "commander_location": "",
                "successor_command": "",
                "liaison_officers": "",
            },
            "signal": {
                "communications": "",
                "frequencies": "",
                "call_signs": "",
                "challenge_password": "",
            },
        },
    }

    COA_COMPARISON_CRITERIA = [
        "suitability",
        "feasibility",
        "acceptability",
        "distinguishability",
        "completeness",
    ]

    def __init__(self):
        self._opords: Dict[str, Dict[str, Any]] = {}

    async def create_opord(self, opord_data: Dict[str, Any]) -> Dict[str, Any]:
        opord_id = str(uuid.uuid4())
        opord = {
            "id": opord_id,
            "operation_name": opord_data.get("operation_name", ""),
            "classification": opord_data.get("classification", "SECRET"),
            "paragraph_1_situation": opord_data.get("paragraph_1_situation", dict(self.OPORD_TEMPLATE["paragraph_1_situation"])),
            "paragraph_2_mission": opord_data.get("paragraph_2_mission", dict(self.OPORD_TEMPLATE["paragraph_2_mission"])),
            "paragraph_3_execution": opord_data.get("paragraph_3_execution", dict(self.OPORD_TEMPLATE["paragraph_3_execution"])),
            "paragraph_4_sustainment": opord_data.get("paragraph_4_sustainment", dict(self.OPORD_TEMPLATE["paragraph_4_sustainment"])),
            "paragraph_5_command_signal": opord_data.get("paragraph_5_command_signal", dict(self.OPORD_TEMPLATE["paragraph_5_command_signal"])),
            "annexes": opord_data.get("annexes", []),
            "status": "DRAFT",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": opord_data.get("created_by", "SYSTEM"),
            "approved_at": None,
            "approved_by": None,
            "distributed_at": None,
            "parent_opord_id": opord_data.get("parent_opord_id"),
        }
        self._opords[opord_id] = opord
        return opord

    async def get_opord(self, opord_id: str) -> Optional[Dict[str, Any]]:
        return self._opords.get(opord_id)

    async def update_paragraph(
        self,
        opord_id: str,
        paragraph: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")

        key = f"paragraph_{paragraph}"
        if key in opord:
            opord[key].update(data)
        return opord

    async def add_annex(self, opord_id: str, annex_data: Dict[str, Any]) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")

        annex = {
            "id": str(uuid.uuid4()),
            "annex_type": annex_data.get("annex_type", ""),
            "title": annex_data.get("title", ""),
            "content": annex_data.get("content", {}),
            "classification": annex_data.get("classification", opord["classification"]),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        opord["annexes"].append(annex)
        return annex

    async def approve_opord(self, opord_id: str, approver: str) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")

        missing = self._check_completeness(opord)
        if missing:
            raise ValueError(f"OPORD incompleta. Secciones faltantes: {missing}")

        opord["status"] = "APPROVED"
        opord["approved_at"] = datetime.now(timezone.utc).isoformat()
        opord["approved_by"] = approver
        return opord

    async def distribute_opord(self, opord_id: str, distribution_list: List[str]) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")
        if opord["status"] != "APPROVED":
            raise ValueError("OPORD debe estar aprobada antes de distribuir")

        opord["status"] = "DISTRIBUTED"
        opord["distributed_at"] = datetime.now(timezone.utc).isoformat()
        opord["distribution_list"] = distribution_list
        return opord

    async def generate_fragord(self, base_opord_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        base = self._opords.get(base_opord_id)
        if not base:
            raise ValueError(f"OPORD base {base_opord_id} no encontrada")

        fragord_data = {
            "operation_name": base["operation_name"],
            "classification": base["classification"],
            "paragraph_1_situation": {**base["paragraph_1_situation"], **changes.get("paragraph_1_situation", {})},
            "paragraph_2_mission": {**base["paragraph_2_mission"], **changes.get("paragraph_2_mission", {})},
            "paragraph_3_execution": {**base["paragraph_3_execution"], **changes.get("paragraph_3_execution", {})},
            "paragraph_4_sustainment": {**base["paragraph_4_sustainment"], **changes.get("paragraph_4_sustainment", {})},
            "paragraph_5_command_signal": {**base["paragraph_5_command_signal"], **changes.get("paragraph_5_command_signal", {})},
            "created_by": base["created_by"],
            "parent_opord_id": base_opord_id,
        }
        return await self.create_opord(fragord_data)

    async def compare_coa(self, coa_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        comparison = {
            "criteria": self.COA_COMPARISON_CRITERIA,
            "coa_evaluations": [],
            "recommendation": "",
        }

        scores = {}
        for coa in coa_list:
            coa_id = coa.get("id", str(uuid.uuid4()))
            evaluation = {"coa_id": coa_id, "name": coa.get("name", ""), "scores": {}}
            total = 0
            for criterion in self.COA_COMPARISON_CRITERIA:
                score = coa.get(criterion, 5)
                evaluation["scores"][criterion] = score
                total += score
            scores[coa_id] = total
            evaluation["total_score"] = total
            comparison["coa_evaluations"].append(evaluation)

        best_id = max(scores, key=scores.get)
        best_coa = next((c for c in coa_list if c.get("id") == best_id), None)
        comparison["recommendation"] = f"COA recomendada: {best_coa.get('name', best_id) if best_coa else best_id}"
        comparison["comparison_matrix"] = self._build_matrix(coa_list)
        return comparison

    async def risk_assessment(self, opord_id: str) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")

        risks = []
        risk_categories = [
            "ENEMY_ACTION",
            "TERRAIN_WEATHER",
            "LOGISTICS",
            "COMMUNICATIONS",
            "PERSONNEL",
            "CIVILIAN",
        ]

        for category in risk_categories:
            risk = {
                "id": str(uuid.uuid4()),
                "category": category,
                "hazard": f"Riesgo en categoria {category}",
                "probability": "MEDIUM",
                "severity": "MEDIUM",
                "risk_level": "MEDIUM",
                "mitigation": "",
                "residual_risk": "LOW",
            }
            risks.append(risk)

        overall_risk = self._calculate_overall_risk(risks)

        return {
            "opord_id": opord_id,
            "operation_name": opord["operation_name"],
            "risks": risks,
            "overall_risk_level": overall_risk,
            "risk_matrix": {
                "high": sum(1 for r in risks if r["risk_level"] == "HIGH"),
                "medium": sum(1 for r in risks if r["risk_level"] == "MEDIUM"),
                "low": sum(1 for r in risks if r["risk_level"] == "LOW"),
            },
            "recommendations": [
                "Implementar medidas de mitigacion para riesgos altos",
                "Monitorear continuamente la situacion",
                "Preparar planes de contingencia",
            ],
        }

    async def generate_sync_matrix(self, opord_id: str) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")

        phases = opord.get("paragraph_3_execution", {}).get("concept_of_operations", {}).get("phases", [])
        if not phases:
            phases = [
                {"name": "Phase I - Deployment", "duration_h": 24},
                {"name": "Phase II - Operations", "duration_h": 48},
                {"name": "Phase III - Consolidation", "duration_h": 12},
            ]

        matrix = {
            "opord_id": opord_id,
            "operation_name": opord["operation_name"],
            "phases": phases,
            "synchronization": [],
        }

        tasks = ["MANEUVER", "FIRES", "PROTECTION", "SUSTAINMENT", "C2"]
        for i, phase in enumerate(phases):
            phase_sync = {
                "phase": phase.get("name", f"Phase {i + 1}"),
                "tasks": {},
            }
            for task in tasks:
                phase_sync["tasks"][task] = {
                    "description": f"{task} en {phase.get('name', '')}",
                    "responsible": "",
                    "start_condition": "",
                    "end_condition": "",
                }
            matrix["synchronization"].append(phase_sync)

        return matrix

    async def validate_opord(self, opord_id: str) -> Dict[str, Any]:
        opord = self._opords.get(opord_id)
        if not opord:
            raise ValueError(f"OPORD {opord_id} no encontrada")

        missing = self._check_completeness(opord)
        warnings = self._check_warnings(opord)

        return {
            "opord_id": opord_id,
            "valid": len(missing) == 0,
            "missing_sections": missing,
            "warnings": warnings,
            "completeness_score": round((1 - len(missing) / 5) * 100, 1),
        }

    def _check_completeness(self, opord: Dict[str, Any]) -> List[str]:
        missing = []
        if not opord.get("paragraph_2_mission", {}).get("mission_statement"):
            missing.append("paragraph_2_mission")
        execution = opord.get("paragraph_3_execution", {})
        if not execution.get("commander_intent", {}).get("purpose"):
            missing.append("paragraph_3_commander_intent")
        if not execution.get("concept_of_operations", {}).get("scheme_of_maneuver"):
            missing.append("paragraph_3_concept_of_operations")
        return missing

    def _check_warnings(self, opord: Dict[str, Any]) -> List[str]:
        warnings = []
        if not opord.get("annexes"):
            warnings.append("Sin anexos definidos")
        sustainment = opord.get("paragraph_4_sustainment", {})
        if not sustainment.get("logistics", {}).get("supply"):
            warnings.append("Plan de suministros no detallado")
        if not sustainment.get("medical", {}).get("evacuation_plan"):
            warnings.append("Plan de evacuacion medica no detallado")
        return warnings

    def _calculate_overall_risk(self, risks: List[Dict[str, Any]]) -> str:
        high_count = sum(1 for r in risks if r.get("risk_level") == "HIGH")
        if high_count >= 2:
            return "HIGH"
        elif high_count == 1:
            return "ELEVATED"
        medium_count = sum(1 for r in risks if r.get("risk_level") == "MEDIUM")
        if medium_count >= 3:
            return "MODERATE"
        return "LOW"

    def _build_matrix(self, coa_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        matrix = {}
        for coa in coa_list:
            coa_id = coa.get("id", "")
            matrix[coa_id] = {
                "name": coa.get("name", ""),
                "scores": {c: coa.get(c, 0) for c in self.COA_COMPARISON_CRITERIA},
            }
        return matrix


enhanced_opord_service = EnhancedOPORDService()
