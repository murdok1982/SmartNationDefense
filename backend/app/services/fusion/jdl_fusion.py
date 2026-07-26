import json
import math
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_RULES_DIR = Path(__file__).parent / "rules"
_SITUATION_RULES_PATH = _RULES_DIR / "situation_rules.json"


def _load_rules() -> dict:
    try:
        with open(_SITUATION_RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("No se pudieron cargar reglas tácticas: %s", e)
        return {}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class Location(BaseModel):
    lat: float
    lon: float
    altitude: float = 0.0


class Entity(BaseModel):
    id: str
    entity_type: str
    location: Location
    source: str
    confidence: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HostileUnit(BaseModel):
    id: str
    unit_type: str
    location: Location
    strength: float
    threat_level: float
    capability: str
    intention: str = "UNKNOWN"


class FriendlyUnit(BaseModel):
    id: str
    unit_type: str
    location: Location
    status: str
    strength: float


class NeutralEntity(BaseModel):
    id: str
    entity_type: str
    location: Location
    description: str


class ThreatZone(BaseModel):
    zone_id: str
    center: Location
    radius_km: float
    threat_level: float
    zone_type: str
    description: str


class Action(BaseModel):
    action_type: str
    priority: int
    description: str
    assigned_unit: Optional[str] = None


class ThreatAssessment(BaseModel):
    threat_level: float
    hostile_units: List[HostileUnit] = Field(default_factory=list)
    friendly_units: List[FriendlyUnit] = Field(default_factory=list)
    neutral_entities: List[NeutralEntity] = Field(default_factory=list)
    threat_zones: List[ThreatZone] = Field(default_factory=list)
    recommended_actions: List[Action] = Field(default_factory=list)
    timestamp: str = ""
    assessment_id: str = ""


class TrackPoint(BaseModel):
    ts: str
    lat: float
    lon: float
    altitude: float = 0.0
    speed_kmh: float = 0.0
    heading_deg: float = 0.0


class SubObjectAssessment(BaseModel):
    signal_measurements: List[dict] = Field(default_factory=list)
    features: Dict[str, Any] = Field(default_factory=dict)
    raw_detections: List[dict] = Field(default_factory=list)
    level: int = 0


class Level2Output(BaseModel):
    formations: List[dict] = Field(default_factory=list)
    movement_patterns: List[dict] = Field(default_factory=list)
    tactical_relationships: List[dict] = Field(default_factory=list)
    situation_description: str = ""


class Level3Output(BaseModel):
    intention: str = "UNKNOWN"
    imminence_min: float = 0.0
    threat_assessment: str = ""
    opportunity_window_min: float = 0.0
    recommended_response: str = ""


class Level4Output(BaseModel):
    sensor_requests: List[dict] = Field(default_factory=list)
    data_fusion_improvements: List[str] = Field(default_factory=list)
    resource_reallocation: List[dict] = Field(default_factory=list)


class JDLFusionPipeline(BaseModel):
    level0: SubObjectAssessment = Field(default_factory=SubObjectAssessment)
    level1: List[Entity] = Field(default_factory=list)
    level2: Level2Output = Field(default_factory=Level2Output)
    level3: Level3Output = Field(default_factory=Level3Output)
    level4: Level4Output = Field(default_factory=Level4Output)
    pipeline_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class JDLFusionEngine:
    SOURCE_WEIGHTS = {
        "SAT": 0.9,
        "OSINT": 0.6,
        "HUMINT": 0.8,
        "SIGINT": 0.85,
        "SENSOR": 0.7,
        "RADAR": 0.88,
        "UAV": 0.8,
        "UNKNOWN": 0.3,
    }

    THREAT_TYPES = {"ARMOR", "INFANTRY", "ARTILLERY", "AIR_DEFENSE", "MISSILE", "UAV", "SPECIAL_FORCES"}
    FRIENDLY_TYPES = {"INFANTRY", "ARMOR", "AVIATION", "ARTILLERY", "LOGISTICS", "COMMAND", "RECON"}

    def __init__(self):
        self.rules = _load_rules()

    def reload_rules(self) -> None:
        self.rules = _load_rules()

    # ── Level 0: Sub-object assessment ──────────────────────────────────
    async def level0_sub_object(
        self, raw_signals: List[dict], detections: List[dict]
    ) -> SubObjectAssessment:
        features: Dict[str, Any] = {}
        if detections:
            confs = [d.get("confidence", 0) for d in detections if "confidence" in d]
            features["mean_confidence"] = sum(confs) / len(confs) if confs else 0.0
            features["detection_count"] = len(detections)
        if raw_signals:
            signal_means = {}
            for sig in raw_signals:
                for k, v in sig.items():
                    if isinstance(v, (int, float)):
                        signal_means.setdefault(k, []).append(v)
            features["signal_summary"] = {
                k: sum(v) / len(v) for k, v in signal_means.items()
            }
        return SubObjectAssessment(
            signal_measurements=raw_signals,
            features=features,
            raw_detections=detections,
        )

    # ── Level 1: Object assessment ──────────────────────────────────────
    async def level1_object(
        self, sub: SubObjectAssessment
    ) -> List[Entity]:
        entities: List[Entity] = []
        for det in sub.raw_detections:
            etype = det.get("entity_type", "UNKNOWN").upper()
            loc = Location(
                lat=det.get("lat", 0.0),
                lon=det.get("lon", 0.0),
                altitude=det.get("altitude", 0.0),
            )
            src = det.get("source", "UNKNOWN")
            base_conf = det.get("confidence", 0.5)
            weight = self.SOURCE_WEIGHTS.get(src, 0.3)
            entity = Entity(
                id=det.get("id", str(uuid.uuid4())),
                entity_type=etype,
                location=loc,
                source=src,
                confidence=round(base_conf * weight, 4),
                metadata=det.get("metadata", {}),
            )
            entities.append(entity)
        return entities

    # ── Level 2: Situation assessment ───────────────────────────────────
    async def level2_situation(
        self, entities: List[Entity]
    ) -> Level2Output:
        rules = self.rules
        formations = self._detect_formations(entities, rules)
        movement_patterns = self._detect_movement_patterns(entities, rules)
        relationships = self._build_tactical_relationships(entities)
        situation = self._describe_situation(formations, movement_patterns)
        return Level2Output(
            formations=formations,
            movement_patterns=movement_patterns,
            tactical_relationships=relationships,
            situation_description=situation,
        )

    def _detect_formations(self, entities: List[Entity], rules: dict) -> List[dict]:
        patterns = rules.get("formation_patterns", [])
        if not patterns:
            return []
        hostiles = [e for e in entities if e.entity_type in self.THREAT_TYPES]
        if len(hostiles) < 2:
            return []
        detected = []
        for pattern in patterns:
            min_units = pattern.get("min_units", 3)
            max_dist = pattern.get("max_distance_km", 1.0)
            if len(hostiles) < min_units:
                continue
            for i in range(len(hostiles) - min_units + 1):
                group = hostiles[i : i + min_units]
                dists = [
                    _haversine_km(
                        group[j].location.lat, group[j].location.lon,
                        group[k].location.lat, group[k].location.lon,
                    )
                    for j in range(len(group))
                    for k in range(j + 1, len(group))
                ]
                if all(d <= max_dist for d in dists):
                    detected.append({
                        "formation": pattern["name"],
                        "units": [e.id for e in group],
                        "centroid_lat": round(sum(e.location.lat for e in group) / len(group), 6),
                        "centroid_lon": round(sum(e.location.lon for e in group) / len(group), 6),
                        "implication": pattern.get("tactical_implication", ""),
                        "confidence": round(min(1.0, len(group) / pattern["min_units"]) * 0.8, 2),
                    })
                    break
        return detected

    def _detect_movement_patterns(self, entities: List[Entity], rules: dict) -> List[dict]:
        patterns = rules.get("movement_patterns", [])
        if not patterns:
            return []
        detected = []
        for entity in entities:
            speed = entity.metadata.get("speed_kmh", 0)
            heading = entity.metadata.get("heading_deg", 0)
            for mp in patterns:
                spd_min = mp.get("speed_kmh_min", 0)
                spd_max = mp.get("speed_kmh_max", float("inf"))
                if spd_min <= speed <= spd_max:
                    detected.append({
                        "entity_id": entity.id,
                        "pattern": mp["name"],
                        "speed_kmh": speed,
                        "implication": mp.get("tactical_implication", ""),
                    })
                    break
        return detected

    def _build_tactical_relationships(self, entities: List[Entity]) -> List[dict]:
        rels = []
        for i, e1 in enumerate(entities):
            for j, e2 in enumerate(entities):
                if i >= j:
                    continue
                dist = _haversine_km(
                    e1.location.lat, e1.location.lon,
                    e2.location.lat, e2.location.lon,
                )
                if dist > 50.0:
                    continue
                rel_type = "SAME_TYPE_FORMATION" if e1.entity_type == e2.entity_type else "COORDINATION"
                rels.append({
                    "source_id": e1.id,
                    "target_id": e2.id,
                    "relationship": rel_type,
                    "distance_km": round(dist, 2),
                    "strength": round(max(0.0, 1.0 - dist / 50.0), 3),
                })
        return rels

    def _describe_situation(self, formations: List[dict], movements: List[dict]) -> str:
        parts = []
        for f in formations:
            parts.append(f"Formación {f['formation']} detectada: {f['implication']}")
        for m in movements:
            parts.append(f"Movimiento {m['pattern']} en {m['entity_id']}: {m['implication']}")
        return " | ".join(parts) if parts else "Sin formaciones o patrones significativos detectados"

    # ── Level 3: Impact assessment ──────────────────────────────────────
    async def level3_impact(
        self, level2: Level2Output
    ) -> Level3Output:
        rules = self.rules
        scenarios = rules.get("threat_scenarios", [])
        intentions_map = rules.get("intention_classification", {})
        intention = "UNKNOWN"
        imminence = 99.0
        response = "Monitoreo continuo"
        threat_assessment_str = "Sin amenazas identificadas"
        opportunity = 60.0

        formation_names = {f["formation"] for f in level2.formations}
        movement_names = {m["pattern"] for m in level2.movement_patterns}

        for scenario in scenarios:
            scenario_indicators = set(scenario.get("indicators", []))
            matched = sum(
                1 for ind in scenario_indicators
                if ind.upper() in formation_names or ind.upper().replace(" ", "_") in movement_names
            )
            if matched >= len(scenario_indicators) * 0.6:
                threat_level = scenario.get("threat_level", 50)
                timeline = scenario.get("timeline_min", 30)
                if threat_level > 70:
                    intention = scenario["name"]
                    imminence = float(timeline)
                    response = scenario.get("response", "ACTIVAR PROTOCOLO")
                    threat_assessment_str = f"Amenaza {scenario['name']} - nivel {threat_level}"
                    opportunity = float(timeline) * 0.5
                    break

        for intent_name, intent_cfg in intentions_map.items():
            indicators = set(intent_cfg.get("indicators", []))
            matched = sum(
                1 for ind in indicators
                if ind.upper() in formation_names or ind.upper().replace(" ", "_") in movement_names
            )
            threshold = intent_cfg.get("confidence_threshold", 0.6)
            ratio = matched / max(len(indicators), 1)
            if ratio >= threshold and ratio > 0:
                intention = intent_name
                break

        return Level3Output(
            intention=intention,
            imminence_min=imminence,
            threat_assessment=threat_assessment_str,
            opportunity_window_min=opportunity,
            recommended_response=response,
        )

    # ── Level 4: Process refinement ─────────────────────────────────────
    async def level4_refinement(
        self, level3: Level3Output, entities: List[Entity]
    ) -> Level4Output:
        sensor_requests = []
        improvements = []
        realloc = []
        if level3.intention in ("ARTILLERIA_DESPLIEGUE", "ASALTO_BLINDADO", "EMBOSCADA_INMINENTE"):
            sensor_requests.append({
                "sensor_type": "RADAR",
                "task": "adquirir_blindados",
                "priority": "HIGH",
                "area": {"radius_km": 10.0},
            })
            improvements.append("Aumentar frecuencia de barrido radar")
            improvements.append("Activar modo de seguimiento múltiple")
        if level3.imminence_min < 15.0:
            sensor_requests.append({
                "sensor_type": "UAV",
                "task": "reconocimiento_visual",
                "priority": "URGENT",
                "area": {"radius_km": 5.0},
            })
            improvements.append("Reducir latencia de fusión a < 1s")
        low_conf = [e for e in entities if e.confidence < 0.5]
        if low_conf:
            for e in low_conf:
                realloc.append({
                    "entity_id": e.id,
                    "action": "reasignar_sensor_alta_resolucion",
                    "reason": f"confianza baja ({e.confidence})",
                })
            improvements.append("Correlación cruzada multi-fuente para entidades de baja confianza")
        return Level4Output(
            sensor_requests=sensor_requests,
            data_fusion_improvements=improvements,
            resource_reallocation=realloc,
        )

    # ── Full pipeline ───────────────────────────────────────────────────
    async def run_full_pipeline(
        self,
        raw_signals: List[dict],
        raw_detections: List[dict],
    ) -> JDLFusionPipeline:
        l0 = await self.level0_sub_object(raw_signals, raw_detections)
        l1 = await self.level1_object(l0)
        l2 = await self.level2_situation(l1)
        l3 = await self.level3_impact(l2)
        l4 = await self.level4_refinement(l3, l1)
        return JDLFusionPipeline(
            level0=l0,
            level1=l1,
            level2=l2,
            level3=l3,
            level4=l4,
        )


class SituationAssessment:
    SOURCE_WEIGHTS = JDLFusionEngine.SOURCE_WEIGHTS
    THREAT_TYPES = JDLFusionEngine.THREAT_TYPES
    FRIENDLY_TYPES = JDLFusionEngine.FRIENDLY_TYPES

    def __init__(self):
        self._jdl = JDLFusionEngine()

    async def assess_threats(self, events: List[Dict[str, Any]]) -> ThreatAssessment:
        hostile_units = []
        friendly_units = []
        neutral_entities = []
        threat_zones = []
        actions = []

        for event in events:
            entity_type = event.get("entity_type", "UNKNOWN").upper()
            loc = Location(
                lat=event.get("lat", 0.0),
                lon=event.get("lon", 0.0),
                altitude=event.get("altitude", 0.0),
            )
            source = event.get("source", "UNKNOWN")
            confidence = event.get("confidence", 0.5) * self.SOURCE_WEIGHTS.get(source, 0.3)

            if entity_type in self.THREAT_TYPES:
                threat_level = self._calculate_threat_level(entity_type, event)
                hostile = HostileUnit(
                    id=event.get("id", str(uuid.uuid4())),
                    unit_type=entity_type,
                    location=loc,
                    strength=event.get("strength", 0.5),
                    threat_level=threat_level,
                    capability=event.get("capability", "UNKNOWN"),
                    intention=event.get("intention", "UNKNOWN"),
                )
                hostile_units.append(hostile)
                zone = ThreatZone(
                    zone_id=str(uuid.uuid4()),
                    center=loc,
                    radius_km=self._threat_radius(entity_type, threat_level),
                    threat_level=threat_level,
                    zone_type=f"{entity_type}_ENGAGEMENT",
                    description=f"Zona de amenaza {entity_type} - Nivel {threat_level:.1f}",
                )
                threat_zones.append(zone)
            elif entity_type in self.FRIENDLY_TYPES:
                friendly = FriendlyUnit(
                    id=event.get("id", str(uuid.uuid4())),
                    unit_type=entity_type,
                    location=loc,
                    status=event.get("status", "ACTIVE"),
                    strength=event.get("strength", 1.0),
                )
                friendly_units.append(friendly)
            else:
                neutral = NeutralEntity(
                    id=event.get("id", str(uuid.uuid4())),
                    entity_type=entity_type,
                    location=loc,
                    description=event.get("description", "Entidad no identificada"),
                )
                neutral_entities.append(neutral)

        overall_threat = self._calculate_overall_threat(hostile_units, friendly_units)
        actions = self._generate_recommendations(hostile_units, friendly_units, threat_zones)

        return ThreatAssessment(
            threat_level=overall_threat,
            hostile_units=hostile_units,
            friendly_units=friendly_units,
            neutral_entities=neutral_entities,
            threat_zones=threat_zones,
            recommended_actions=actions,
            timestamp=datetime.now(timezone.utc).isoformat(),
            assessment_id=str(uuid.uuid4()),
        )

    async def identify_relationships(self, entities: List[Dict[str, Any]]):
        from pydantic import BaseModel
        class Relationship(BaseModel):
            source_id: str
            target_id: str
            relationship_type: str
            strength: float
            metadata: dict = Field(default_factory=dict)
        class RelationshipGraph(BaseModel):
            nodes: List[dict] = Field(default_factory=list)
            edges: List[Relationship] = Field(default_factory=list)

        nodes = []
        edges = []
        for e in entities:
            nodes.append({
                "id": e.get("id", str(uuid.uuid4())),
                "entity_type": e.get("entity_type", "UNKNOWN"),
                "lat": e.get("lat", 0.0),
                "lon": e.get("lon", 0.0),
                "source": e.get("source", "UNKNOWN"),
                "confidence": e.get("confidence", 0.5),
            })
        for i, n1 in enumerate(nodes):
            for j, n2 in enumerate(nodes):
                if i >= j:
                    continue
                distance = _haversine_km(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
                if distance < 50.0:
                    rel_type = "SAME_TYPE_FORMATION" if n1["entity_type"] == n2["entity_type"] else "COORDINATION"
                    strength = round(max(0.0, 1.0 - distance / 50.0), 3)
                    edges.append(Relationship(
                        source_id=n1["id"],
                        target_id=n2["id"],
                        relationship_type=rel_type,
                        strength=strength,
                        metadata={"distance_km": round(distance, 2)},
                    ))
        return RelationshipGraph(nodes=nodes, edges=edges)

    async def evaluate_intentions(self, enemy_units: List[Dict[str, Any]]):
        class IntentionAnalysis(BaseModel):
            unit_id: str
            predicted_intention: str
            confidence: float
            indicators: List[str] = Field(default_factory=list)
            course_of_action: str = "UNKNOWN"

        analyses = []
        for unit in enemy_units:
            indicators = []
            predicted_intention = "UNKNOWN"
            confidence = 0.3
            unit_type = unit.get("entity_type", "").upper()
            speed = unit.get("speed", 0)
            proximity = unit.get("proximity_to_objective", 100)

            if unit_type == "ARMOR" and speed > 20:
                predicted_intention = "ADVANCE"
                confidence = 0.7
                indicators.append("Movimiento rapido de blindados")
            elif unit_type == "ARTILLERY" and unit.get("deployment_status") == "DEPLOYED":
                predicted_intention = "FIRE_MISSION"
                confidence = 0.8
                indicators.append("Artilleria desplegada")
            elif unit_type == "INFANTRY" and proximity < 10:
                predicted_intention = "ASSAULT"
                confidence = 0.6
                indicators.append("Infanteria proxima a objetivo")
            elif unit_type == "AIR_DEFENSE":
                predicted_intention = "AREA_DENIAL"
                confidence = 0.75
                indicators.append("Sistema de defensa aerea activo")
            elif speed < 5 and unit_type == "ARMOR":
                predicted_intention = "DEFEND"
                confidence = 0.5
                indicators.append("Blindados estaticos")

            analyses.append(IntentionAnalysis(
                unit_id=unit.get("id", str(uuid.uuid4())),
                predicted_intention=predicted_intention,
                confidence=confidence,
                indicators=indicators,
                course_of_action=predicted_intention,
            ))
        return analyses

    async def generate_ctp(self, events: List[Dict[str, Any]]):
        class CommonTacticalPicture(BaseModel):
            assessment: ThreatAssessment
            relationships: Any
            intentions: Any
            generated_at: str
            version: int = 1

        assessment = await self.assess_threats(events)
        relationships = await self.identify_relationships(events)
        intentions = await self.evaluate_intentions(events)

        return CommonTacticalPicture(
            assessment=assessment,
            relationships=relationships,
            intentions=intentions,
            generated_at=datetime.now(timezone.utc).isoformat(),
            version=1,
        )

    def _calculate_threat_level(self, entity_type: str, event: Dict) -> float:
        base = {"ARMOR": 75.0, "INFANTRY": 50.0, "ARTILLERY": 85.0,
                "AIR_DEFENSE": 90.0, "MISSILE": 95.0, "UAV": 60.0,
                "SPECIAL_FORCES": 70.0}.get(entity_type, 30.0)
        return min(100.0, base + event.get("strength", 0.5) * 20 + max(0, 30 - event.get("distance_to_friendly", 50)))

    def _calculate_overall_threat(self, hostiles: List[HostileUnit], friendlies: List[FriendlyUnit]) -> float:
        if not hostiles:
            return 0.0
        total_h = sum(h.threat_level * h.strength for h in hostiles)
        total_f = sum(f.strength for f in friendlies) if friendlies else 1.0
        return min(100.0, (total_h / max(total_f, 0.1)) * 25)

    def _threat_radius(self, entity_type: str, threat_level: float) -> float:
        base = {"ARMOR": 15.0, "INFANTRY": 5.0, "ARTILLERY": 40.0,
                "AIR_DEFENSE": 80.0, "MISSILE": 200.0, "UAV": 25.0,
                "SPECIAL_FORCES": 10.0}.get(entity_type, 10.0)
        return base * (threat_level / 50.0)

    def _generate_recommendations(
        self, hostiles: List[HostileUnit], friendlies: List[FriendlyUnit],
        zones: List[ThreatZone],
    ) -> List[Action]:
        actions = []
        if any(h.threat_level > 70 for h in hostiles):
            actions.append(Action(action_type="ENGAGE_HIGH_PRIORITY", priority=1,
                                  description="Neutralizar amenazas de alta prioridad"))
        if any(z.zone_type == "AIR_DEFENSE_ENGAGEMENT" for z in zones):
            actions.append(Action(action_type="SEAD_MISSION", priority=1,
                                  description="Mision SEAD contra defensa aerea"))
        if len(hostiles) > len(friendlies) * 1.5:
            actions.append(Action(action_type="REQUEST_REINFORCEMENTS", priority=2,
                                  description="Solicitar refuerzos - superioridad enemiga"))
        if not actions:
            actions.append(Action(action_type="MAINTAIN_POSTURE", priority=3,
                                  description="Mantener postura defensiva"))
        return actions


jdl_fusion_engine = SituationAssessment()
jdl_pipeline = JDLFusionEngine()
