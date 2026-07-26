import math
import logging
from typing import Dict, Any, List

from app.services.tactical.coa_engine import COAEngine, CourseOfAction, MissionParams
from app.services.fusion.jdl_fusion import jdl_fusion_engine
from app.services.terrain.service import terrain_service

logger = logging.getLogger(__name__)


class WargamingSimulator:
    """Simulador de Cursos de Accion para wargaming tactico.

    Utiliza datos reales del COAEngine, JDLFusionEngine y TerrainService.
    Resultados deterministas basados en el estado actual del campo de batalla.
    """

    def __init__(self):
        self.coa_engine = COAEngine()

    async def simulate_coa(
        self, coa: CourseOfAction, mission: MissionParams
    ) -> Dict[str, Any]:
        if not coa.phases:
            raise ValueError("El COA no contiene fases")

        situation = await jdl_fusion_engine.assess_threats(
            [
                {
                    "entity_type": "ARMOR",
                    "lat": phase.key_terrain[0].get("lat", 0.0) if phase.key_terrain else 0.0,
                    "lon": phase.key_terrain[0].get("lon", 0.0) if phase.key_terrain else 0.0,
                    "source": "WARGAMING",
                    "confidence": 1.0,
                }
                for phase in coa.phases
                if phase.key_terrain
            ]
        )

        phase_results = []
        for phase in coa.phases:
            phase_result = await self._evaluate_phase(phase, coa, mission, situation)
            phase_results.append(phase_result)

        hostile_count = len(situation.hostile_units)
        friendly_count = max(len(mission.forces_available), 1)
        force_ratio = friendly_count / max(hostile_count, 1)

        total_exposure = sum(
            1 for r in coa.routes if r.exposure_level in ("HIGH", "CRITICAL")
        )
        exposure_factor = total_exposure / max(len(coa.routes), 1)

        try:
            terrain_analysis = await terrain_service.terrain_analysis(
                {
                    "center_lat": mission.objective.get("lat", 0.0),
                    "center_lon": mission.objective.get("lon", 0.0),
                    "radius_km": 10.0,
                }
            )
            los_coverage = terrain_analysis.get("coverage_analysis", {}).get(
                "los_coverage_pct", 50.0
            )
            cover_factor = (100.0 - los_coverage) / 100.0
        except Exception as e:
            logger.warning("Terrain analysis no disponible: %s", e)
            cover_factor = 0.5

        success_probability = round(
            (force_ratio * 0.3)
            + (cover_factor * 0.25)
            + ((1.0 - exposure_factor) * 0.25)
            + ((100.0 - situation.threat_level) / 100.0 * 0.2),
            2,
        )
        success_probability = max(0.0, min(1.0, success_probability))

        total_casualties = sum(p["estimated_casualties"] for p in phase_results)
        total_duration = coa.estimated_duration_min

        risks = []
        if situation.threat_level > 70:
            risks.append("superioridad_enemiga")
        if exposure_factor > 0.5:
            risks.append("alta_exposicion_fuego")
        if cover_factor < 0.3:
            risks.append("terreno_descubierto_sin_cobertura")
        if hostile_count > friendly_count * 1.5:
            risks.append("desventaja_numerica")

        return {
            "coa_id": coa.id,
            "coa_name": coa.name,
            "success_probability": success_probability,
            "estimated_casualties": total_casualties,
            "estimated_duration_hours": round(total_duration / 60, 1),
            "phase_count": len(coa.phases),
            "phase_results": phase_results,
            "threat_level": round(situation.threat_level, 1),
            "force_ratio": round(force_ratio, 2),
            "cover_factor": round(cover_factor, 2),
            "hostile_units": hostile_count,
            "friendly_units": friendly_count,
            "risks": risks,
        }

    async def _evaluate_phase(
        self,
        phase: Any,
        coa: CourseOfAction,
        mission: MissionParams,
        situation: Any,
    ) -> Dict[str, Any]:
        phase_exposure = 0.0
        for route in coa.routes:
            los_result = await terrain_service.line_of_sight(
                observer={"lat": route.start.get("lat", 0.0), "lon": route.start.get("lon", 0.0)},
                target={
                    "lat": route.end.get("lat", 0.0),
                    "lon": route.end.get("lon", 0.0),
                },
                observer_height_m=3.0,
                target_height_m=1.5,
            )
            if los_result.get("visible"):
                phase_exposure += 1.0

        phase_exposure = phase_exposure / max(len(coa.routes), 1)

        phase_hostiles = sum(
            1
            for h in situation.hostile_units
            if any(
                _haversine_km(
                    h.location.lat, h.location.lon,
                    kt.get("lat", 0.0), kt.get("lon", 0.0),
                ) < 10.0
                for kt in phase.key_terrain
            )
        )
        phase_forces = len(phase.forces_assigned)
        phase_ratio = phase_forces / max(phase_hostiles, 1)

        casualties = int(
            max(1, phase_ratio * 5.0 * (1.0 + phase_exposure))
        )

        return {
            "phase_name": phase.name,
            "phase_objective": phase.objective,
            "duration_min": phase.duration_min,
            "exposure": round(phase_exposure, 2),
            "force_ratio": round(phase_ratio, 2),
            "estimated_casualties": casualties,
        }

    async def compare_coas(
        self, coas: List[CourseOfAction], mission: MissionParams
    ) -> List[Dict[str, Any]]:
        results = []
        for coa in coas:
            result = await self.simulate_coa(coa, mission)
            results.append(result)
        return sorted(
            results, key=lambda x: x["success_probability"], reverse=True
        )

    async def monte_carlo(
        self, mission: MissionParams, iterations: int = 1000
    ) -> Dict[str, Any]:
        raise NotImplementedError(
            "Requiere motor de simulacion distribuida. "
            "Considere integrar con Apache Spark o Ray para simulaciones paralelas."
        )


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


wargaming = WargamingSimulator()
