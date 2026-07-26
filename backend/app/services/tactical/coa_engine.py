# -*- coding: utf-8 -*-
import json
import math
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from pydantic import BaseModel, Field

from app.services.terrain.service import terrain_service, _haversine_km, GeoPoint

_RULES_DIR = Path(__file__).resolve().parent / "rules"
_TEMPLATES_PATH = _RULES_DIR / "coa_templates.json"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReadinessLevel(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"


class TerrainType(str, Enum):
    PLAIN = "PLAIN"
    LOWLAND = "LOWLAND"
    HILLS = "HILLS"
    MOUNTAIN = "MOUNTAIN"


Waypoint = Dict[str, float]


class MissionParams(BaseModel):
    objective: Dict[str, float] = Field(..., description="Objetivo {lat, lon}")
    forces_available: List[str] = Field(default_factory=list, description="IDs de unidades ORBAT disponibles")
    time_window_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time_window_end: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(hour=23, minute=59))
    rules_of_engagement: str = Field(default="STANDING", description="Reglas de enfrentamiento")
    priority: int = Field(default=3, ge=1, le=5, description="1=máxima prioridad")
    start_position: Dict[str, float] = Field(default_factory=lambda: {"lat": 0.0, "lon": 0.0})
    threat_intel: Dict[str, Any] = Field(default_factory=dict)


class COAPhase(BaseModel):
    name: str
    objective: str
    forces_assigned: List[str] = Field(default_factory=list)
    start_offset_min: int = 0
    duration_min: int = 30
    key_terrain: List[Dict[str, Any]] = Field(default_factory=list)
    fires_plan: Dict[str, Any] = Field(default_factory=dict)


class RouteSegment(BaseModel):
    start: Waypoint
    end: Waypoint
    distance_km: float = 0.0
    terrain_type: str = "PLAIN"
    exposure_level: str = "LOW"
    alternative_routes: List[Waypoint] = Field(default_factory=list)


class CourseOfAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    template_id: str = ""
    phases: List[COAPhase] = Field(default_factory=list)
    routes: List[RouteSegment] = Field(default_factory=list)
    risk_score: float = 0.0
    weapon_score: float = 0.0
    overall_score: float = 0.0
    estimated_casualties: int = 0
    estimated_duration_min: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RiskFactor(BaseModel):
    name: str
    probability: float = Field(..., ge=0.0, le=1.0)
    impact: float = Field(..., ge=0.0, le=1.0)
    score: float = 0.0
    description: str = ""


class RiskAssessment(BaseModel):
    coa_id: str = ""
    overall_level: RiskLevel = RiskLevel.LOW
    factors: List[RiskFactor] = Field(default_factory=list)
    mitigation_suggestions: List[str] = Field(default_factory=list)


class WeaponStatus(BaseModel):
    required: int = 0
    available: int = 0
    operational: int = 0
    readiness_pct: float = 0.0


class WeaponAssessment(BaseModel):
    coa_id: str = ""
    overall_readiness: float = 0.0
    overall_status: ReadinessLevel = ReadinessLevel.GREEN
    by_type: Dict[str, WeaponStatus] = Field(default_factory=dict)
    critical_shortfalls: List[str] = Field(default_factory=list)


class ComparisonCriteria(BaseModel):
    weight_risk: float = Field(default=0.25, ge=0, le=1)
    weight_time: float = Field(default=0.15, ge=0, le=1)
    weight_casualties: float = Field(default=0.20, ge=0, le=1)
    weight_success: float = Field(default=0.30, ge=0, le=1)
    weight_logistics: float = Field(default=0.10, ge=0, le=1)


class ScoredCOA(BaseModel):
    coa: CourseOfAction
    score: float = 0.0
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)


class COAEngine:
    def __init__(self):
        self._templates: List[Dict[str, Any]] = []
        self._load_templates()

    # ── Template loading ──

    def _load_templates(self) -> None:
        try:
            data = json.loads(_TEMPLATES_PATH.read_text(encoding="utf-8"))
            self._templates = data.get("templates", [])
        except (FileNotFoundError, json.JSONDecodeError):
            self._templates = []

    def get_templates(self) -> List[Dict[str, Any]]:
        return list(self._templates)

    def get_templates_for_terrain(self, terrain: str) -> List[Dict[str, Any]]:
        return [t for t in self._templates if terrain in t.get("suitable_terrain", [])]

    # ── COA generation ──

    async def generate_coas(self, mission: MissionParams) -> List[CourseOfAction]:
        coas: List[CourseOfAction] = []
        terrain_type = await self._classify_area_terrain(mission.objective)
        suitable = self.get_templates_for_terrain(terrain_type) or self._templates

        for tpl in suitable:
            coa = await self._build_from_template(tpl, mission)
            route = await self._compute_route(mission, coa)
            coa.routes = route
            coa.estimated_duration_min = sum(p.duration_min for p in coa.phases) + int(
                sum(r.distance_km for r in route) * 1.5
            )
            coa.estimated_casualties = self._estimate_casualties(coa, mission)
            risk = await self.assess_risk(coa, mission)
            coa.risk_score = risk.overall_level.value
            weapon = await self.assess_weapon_availability(coa)
            coa.weapon_score = weapon.overall_readiness
            coas.append(coa)

        if not coas:
            coas.append(await self._build_default_coa(mission))

        return coas

    async def _build_from_template(
        self, tpl: Dict[str, Any], mission: MissionParams
    ) -> CourseOfAction:
        phases = []
        for i, p in enumerate(tpl.get("phases", [])):
            phases.append(
                COAPhase(
                    name=p["name"],
                    objective=f"Fase {i+1}: {p['name']}",
                    forces_assigned=list(mission.forces_available),
                    start_offset_min=p.get("order", i + 1) * p.get("duration_min", 30),
                    duration_min=p.get("duration_min", 30),
                    key_terrain=[{"lat": mission.objective.get("lat"), "lon": mission.objective.get("lon")}],
                    fires_plan={"template": tpl["id"], "phase": i},
                )
            )

        return CourseOfAction(
            name=tpl.get("name", "COA sin nombre"),
            template_id=tpl.get("id", "unknown"),
            phases=phases,
        )

    async def _build_default_coa(self, mission: MissionParams) -> CourseOfAction:
        return CourseOfAction(
            name="COA por defecto",
            template_id="default",
            phases=[
                COAPhase(
                    name="Avance y asalto",
                    objective="Alcanzar y neutralizar objetivo",
                    forces_assigned=list(mission.forces_available),
                    duration_min=120,
                )
            ],
        )

    async def _compute_route(
        self, mission: MissionParams, coa: CourseOfAction
    ) -> List[RouteSegment]:
        start = mission.start_position
        end = mission.objective
        segments: List[RouteSegment] = []

        if not start.get("lat") or not end.get("lat"):
            return segments

        try:
            result = await terrain_service.route_analysis(
                start=start, end=end, vehicle_type="MOTORIZED"
            )
            for seg_data in result.get("segments", []):
                terrain = seg_data.get("terrain_type", "PLAIN")
                exposure = self._calc_exposure(seg_data)
                segments.append(
                    RouteSegment(
                        start=seg_data["start"],
                        end=seg_data["end"],
                        distance_km=seg_data.get("distance_km", 0),
                        terrain_type=terrain,
                        exposure_level=exposure,
                    )
                )
        except Exception:
            direct_km = _haversine_km(
                GeoPoint(lat=start.get("lat", 0), lon=start.get("lon", 0)),
                GeoPoint(lat=end.get("lat", 0), lon=end.get("lon", 0)),
            )
            segments.append(
                RouteSegment(
                    start=start,
                    end=end,
                    distance_km=round(direct_km, 3),
                    terrain_type="PLAIN",
                    exposure_level="MEDIUM",
                )
            )

        return segments

    async def _classify_area_terrain(self, objective: Dict[str, float]) -> str:
        lat = objective.get("lat", 0)
        lon = objective.get("lon", 0)
        try:
            elev_data = await terrain_service.get_elevation(lat, lon)
            elev = elev_data.get("elevation_m", 0)
            if elev < 50:
                return "LOWLAND"
            elif elev < 150:
                return "PLAIN"
            elif elev < 300:
                return "HILLS"
            else:
                return "MOUNTAIN"
        except Exception:
            return "PLAIN"

    def _calc_exposure(self, seg: Dict[str, Any]) -> str:
        obstacles = seg.get("obstacles", [])
        terrain = seg.get("terrain_type", "PLAIN")
        if obstacles or terrain in ("PLAIN",):
            return "HIGH"
        if terrain in ("LOWLAND",):
            return "MEDIUM"
        return "LOW"

    def _estimate_casualties(self, coa: CourseOfAction, mission: MissionParams) -> int:
        total_forces = max(len(mission.forces_available), 1)
        estimated_enemy = len(mission.threat_intel) if mission.threat_intel else total_forces
        force_ratio = total_forces / max(estimated_enemy, 1)

        exposed_segments = sum(
            1 for r in coa.routes if r.exposure_level in ("HIGH", "CRITICAL")
        )
        exposure_factor = exposed_segments / max(len(coa.routes), 1)

        mission_map = {"RECON": 0.3, "ASSAULT": 1.2, "AMBUSH": 1.0, "PATROL": 0.6, "SECURE": 0.8}
        mission_type = getattr(mission, "rules_of_engagement", None)
        mission_factor = mission_map.get(mission_type, 1.0) if mission_type else 1.0

        base_casualties = 10.0 * len(coa.phases)
        force_ratio_factor = min(2.0, 1.0 / max(force_ratio, 0.1))
        casualties = base_casualties * exposure_factor * mission_factor * force_ratio_factor
        return max(1, int(casualties))

    # ── Risk assessment ──

    async def assess_risk(
        self,
        coa: CourseOfAction,
        mission: Optional[MissionParams] = None,
    ) -> RiskAssessment:
        factors: List[RiskFactor] = []

        exposure_factor = await self._assess_exposure_risk(coa)
        factors.append(exposure_factor)

        extraction_factor = await self._assess_extraction_risk(coa)
        factors.append(extraction_factor)

        time_factor = self._assess_time_risk(coa, mission)
        factors.append(time_factor)

        threat_factor = self._assess_threat_risk(mission)
        factors.append(threat_factor)

        for f in factors:
            f.score = round(f.probability * f.impact * 100, 1)

        overall_score = sum(f.score for f in factors) / max(len(factors), 1)
        overall_level = self._score_to_risk_level(overall_score)

        mitigations = self._generate_mitigations(factors, overall_level)

        return RiskAssessment(
            coa_id=coa.id,
            overall_level=overall_level,
            factors=factors,
            mitigation_suggestions=mitigations,
        )

    async def _assess_exposure_risk(self, coa: CourseOfAction) -> RiskFactor:
        exposed_segments = sum(
            1 for r in coa.routes if r.exposure_level in ("HIGH", "CRITICAL")
        )
        total = max(len(coa.routes), 1)
        prob = min(1.0, exposed_segments / total * 0.8)
        impact = 0.7 if exposed_segments > 0 else 0.3
        return RiskFactor(
            name="Exposición a fuego enemigo",
            probability=round(prob, 2),
            impact=round(impact, 2),
            description=f"{exposed_segments}/{total} segmentos con alta exposición",
        )

    async def _assess_extraction_risk(self, coa: CourseOfAction) -> RiskFactor:
        phase_count = len(coa.phases)
        has_extraction = any(
            "extracción" in p.name.lower() or "consolidación" in p.name.lower()
            for p in coa.phases
        )
        prob = 0.2 if has_extraction else 0.7
        impact = 0.8 if phase_count > 3 else 0.5
        return RiskFactor(
            name="Disponibilidad de rutas de extracción",
            probability=round(prob, 2),
            impact=round(impact, 2),
            description="Incluida" if has_extraction else "No planificada explícitamente",
        )

    def _assess_time_risk(
        self, coa: CourseOfAction, mission: Optional[MissionParams]
    ) -> RiskFactor:
        estimated = coa.estimated_duration_min
        if mission and mission.time_window_start and mission.time_window_end:
            available = (mission.time_window_end - mission.time_window_start).total_seconds() / 60
            ratio = estimated / max(available, 1)
            prob = min(1.0, ratio)
        else:
            prob = 0.3
        return RiskFactor(
            name="Tiempo estimado vs ventana operacional",
            probability=round(prob, 2),
            impact=round(0.6, 2),
            description=f"Estimado: {estimated} min",
        )

    def _assess_threat_risk(self, mission: Optional[MissionParams]) -> RiskFactor:
        if mission and mission.threat_intel:
            threat_level = mission.threat_intel.get("level", 0.5)
            prob = min(1.0, threat_level)
            desc = mission.threat_intel.get("summary", "Intel disponible")
        else:
            prob = 0.3
            desc = "Sin intel de amenazas reciente"
        return RiskFactor(
            name="Intel reciente de amenazas",
            probability=round(prob, 2),
            impact=round(0.5, 2),
            description=desc,
        )

    @staticmethod
    def _score_to_risk_level(score: float) -> RiskLevel:
        if score >= 70:
            return RiskLevel.CRITICAL
        elif score >= 40:
            return RiskLevel.HIGH
        elif score >= 20:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @staticmethod
    def _generate_mitigations(
        factors: List[RiskFactor], level: RiskLevel
    ) -> List[str]:
        suggestions = []
        for f in factors:
            if f.score >= 50:
                suggestions.append(
                    f"Mitigar '{f.name}': {f.description}"
                )
        if level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            suggestions.append("Considerar COA alternativo con menor perfil de riesgo")
            suggestions.append("Solicitar apoyo de fuegos adicional antes del despliegue")
        if not suggestions:
            suggestions.append("Perfil de riesgo aceptable — proceder con la ejecución planificada")
        return suggestions

    # ── Weapon availability ──

    async def assess_weapon_availability(self, coa: CourseOfAction) -> WeaponAssessment:
        by_type: Dict[str, WeaponStatus] = {}

        try:
            from app.db.session import async_session_factory
            from app.db.models.persistence import Asset
            from sqlalchemy import select

            async with async_session_factory() as db:
                result = await db.execute(
                    select(Asset).where(Asset.kind.in_(["weapon", "munitions", "ordnance"]))
                )
                db_assets = result.scalars().all()
        except Exception:
            db_assets = []

        for phase in coa.phases:
            fires = phase.fires_plan or {}
            weapons_needed = fires.get("weapons", ["small_arms", "artillery", "mortar"])
            if isinstance(weapons_needed, str):
                weapons_needed = ["small_arms"]
            for w in weapons_needed:
                if w not in by_type:
                    available_count = sum(
                        1 for a in db_assets
                        if a.current_status == "OPERATIONAL"
                        and (w in (a.kind or "").lower() or w in (a.metadata_json or {}).get("type", "").lower())
                    )
                    operational_count = sum(
                        1 for a in db_assets
                        if a.current_status == "OPERATIONAL"
                        and (w in (a.kind or "").lower() or w in (a.metadata_json or {}).get("type", "").lower())
                    )
                    by_type[w] = WeaponStatus(
                        required=0,
                        available=available_count,
                        operational=operational_count,
                        readiness_pct=0.0,
                    )
                by_type[w].required += 1

        for w in by_type:
            ws = by_type[w]
            if ws.required > 0:
                avail_ratio = ws.available / ws.required
                op_ratio = ws.operational / max(ws.available, 1)
                ws.readiness_pct = round((avail_ratio * 0.4 + op_ratio * 0.6) * 100, 1)
            else:
                ws.readiness_pct = 100.0

        if by_type:
            overall = sum(ws.readiness_pct for ws in by_type.values()) / len(by_type)
        else:
            overall = 100.0

        status = ReadinessLevel.GREEN
        if overall < 50:
            status = ReadinessLevel.RED
        elif overall < 75:
            status = ReadinessLevel.AMBER

        shortfalls = [
            f"{w}: disponible {ws.available}/{ws.required}"
            for w, ws in by_type.items()
            if ws.available < ws.required
        ]

        return WeaponAssessment(
            coa_id=coa.id,
            overall_readiness=round(overall, 1),
            overall_status=status,
            by_type=by_type,
            critical_shortfalls=shortfalls,
        )

    # ── COA comparison ──

    async def compare_coas(
        self,
        coas: List[CourseOfAction],
        criteria: ComparisonCriteria,
        mission: Optional[MissionParams] = None,
    ) -> List[ScoredCOA]:
        if not coas:
            return []

        risks = [await self.assess_risk(c, mission) for c in coas]
        weapons = [await self.assess_weapon_availability(c) for c in coas]

        norm_risk = self._normalize([r.overall_level.value for r in risks])
        norm_time = self._normalize([c.estimated_duration_min for c in coas])
        norm_casualties = self._normalize([c.estimated_casualties for c in coas])
        norm_success = self._normalize([-c.risk_score for c in coas])
        norm_logistics = self._normalize([w.overall_readiness for w in weapons])

        results: List[ScoredCOA] = []
        for i, coa in enumerate(coas):
            score = (
                (1 - norm_risk[i]) * criteria.weight_risk
                + (1 - norm_time[i]) * criteria.weight_time
                + (1 - norm_casualties[i]) * criteria.weight_casualties
                + norm_success[i] * criteria.weight_success
                + norm_logistics[i] * criteria.weight_logistics
            ) * 100

            strengths, weaknesses = self._evaluate_strengths_weaknesses(
                coa, risks[i], weapons[i], norm_risk[i], norm_logistics[i]
            )

            coa.overall_score = round(score, 1)
            results.append(
                ScoredCOA(
                    coa=coa,
                    score=round(score, 1),
                    strengths=strengths,
                    weaknesses=weaknesses,
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    @staticmethod
    def _normalize(values: List[float]) -> List[float]:
        if not values:
            return []
        mn, mx = min(values), max(values)
        if mx == mn:
            return [0.5] * len(values)
        return [(v - mn) / (mx - mn) for v in values]

    @staticmethod
    def _evaluate_strengths_weaknesses(
        coa: CourseOfAction,
        risk: RiskAssessment,
        weapon: WeaponAssessment,
        norm_risk: float,
        norm_logistics: float,
    ) -> Tuple[List[str], List[str]]:
        strengths = []
        weaknesses = []

        if risk.overall_level in (RiskLevel.LOW, RiskLevel.MEDIUM):
            strengths.append("Perfil de riesgo bajo/medio")
        else:
            weaknesses.append(f"Alto riesgo ({risk.overall_level.value})")

        if weapon.overall_status == ReadinessLevel.GREEN:
            strengths.append("Disponibilidad de armamento óptima")
        elif weapon.overall_status == ReadinessLevel.RED:
            weaknesses.append("Carencias críticas de armamento")

        if weapon.critical_shortfalls:
            weaknesses.append(f"Carencias: {'; '.join(weapon.critical_shortfalls[:3])}")

        if norm_logistics >= 0.7:
            strengths.append("Alta preparación logística")

        if coa.estimated_duration_min <= 120:
            strengths.append("Operación de corta duración")
        elif coa.estimated_duration_min > 360:
            weaknesses.append("Duración extendida (>6h)")

        if not strengths:
            strengths.append("Sin fortalezas significativas identificadas")
        if not weaknesses:
            weaknesses.append("Sin debilidades significativas identificadas")

        return strengths, weaknesses


coa_engine = COAEngine()
