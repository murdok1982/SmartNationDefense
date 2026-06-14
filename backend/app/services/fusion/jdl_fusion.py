# -*- coding: utf-8 -*-
import uuid
import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Location:
    lat: float
    lon: float
    altitude: float = 0.0


@dataclass
class Entity:
    id: str
    entity_type: str
    location: Location
    source: str
    confidence: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HostileUnit:
    id: str
    unit_type: str
    location: Location
    strength: float
    threat_level: float
    capability: str
    intention: str = "UNKNOWN"


@dataclass
class FriendlyUnit:
    id: str
    unit_type: str
    location: Location
    status: str
    strength: float


@dataclass
class NeutralEntity:
    id: str
    entity_type: str
    location: Location
    description: str


@dataclass
class ThreatZone:
    zone_id: str
    center: Location
    radius_km: float
    threat_level: float
    zone_type: str
    description: str


@dataclass
class Action:
    action_type: str
    priority: int
    description: str
    assigned_unit: Optional[str] = None


@dataclass
class ThreatAssessment:
    threat_level: float
    hostile_units: List[HostileUnit] = field(default_factory=list)
    friendly_units: List[FriendlyUnit] = field(default_factory=list)
    neutral_entities: List[NeutralEntity] = field(default_factory=list)
    threat_zones: List[ThreatZone] = field(default_factory=list)
    recommended_actions: List[Action] = field(default_factory=list)
    timestamp: str = ""
    assessment_id: str = ""


@dataclass
class Relationship:
    source_id: str
    target_id: str
    relationship_type: str
    strength: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationshipGraph:
    nodes: List[Entity] = field(default_factory=list)
    edges: List[Relationship] = field(default_factory=list)


@dataclass
class IntentionAnalysis:
    unit_id: str
    predicted_intention: str
    confidence: float
    indicators: List[str] = field(default_factory=list)
    course_of_action: str = "UNKNOWN"


@dataclass
class CommonTacticalPicture:
    assessment: ThreatAssessment
    relationships: RelationshipGraph
    intentions: List[IntentionAnalysis]
    generated_at: str
    version: int = 1


def _haversine_km(loc1: Location, loc2: Location) -> float:
    R = 6371.0
    lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
    lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class SituationAssessment:
    SOURCE_WEIGHTS = {
        "SAT": 0.9,
        "OSINT": 0.6,
        "HUMINT": 0.8,
        "SIGINT": 0.85,
        "SENSOR": 0.7,
        "UNKNOWN": 0.3,
    }

    THREAT_TYPES = {"ARMOR", "INFANTRY", "ARTILLERY", "AIR_DEFENSE", "MISSILE", "UAV", "SPECIAL_FORCES"}
    FRIENDLY_TYPES = {"INFANTRY", "ARMOR", "AVIATION", "ARTILLERY", "LOGISTICS", "COMMAND", "RECON"}

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

    async def identify_relationships(self, entities: List[Dict[str, Any]]) -> RelationshipGraph:
        nodes = []
        edges = []

        for e in entities:
            loc = Location(lat=e.get("lat", 0.0), lon=e.get("lon", 0.0))
            node = Entity(
                id=e.get("id", str(uuid.uuid4())),
                entity_type=e.get("entity_type", "UNKNOWN"),
                location=loc,
                source=e.get("source", "UNKNOWN"),
                confidence=e.get("confidence", 0.5),
            )
            nodes.append(node)

        for i, e1 in enumerate(nodes):
            for j, e2 in enumerate(nodes):
                if i >= j:
                    continue
                distance = _haversine_km(e1.location, e2.location)
                if distance < 50.0:
                    rel_type = self._determine_relationship(e1, e2, distance)
                    strength = max(0.0, 1.0 - (distance / 50.0))
                    edge = Relationship(
                        source_id=e1.id,
                        target_id=e2.id,
                        relationship_type=rel_type,
                        strength=round(strength, 3),
                        metadata={"distance_km": round(distance, 2)},
                    )
                    edges.append(edge)

        return RelationshipGraph(nodes=nodes, edges=edges)

    async def evaluate_intentions(self, enemy_units: List[Dict[str, Any]]) -> List[IntentionAnalysis]:
        analyses = []
        for unit in enemy_units:
            indicators = []
            predicted_intention = "UNKNOWN"
            confidence = 0.3

            unit_type = unit.get("entity_type", "").upper()
            speed = unit.get("speed", 0)
            heading = unit.get("heading", 0)
            proximity_to_objective = unit.get("proximity_to_objective", 100)

            if unit_type == "ARMOR" and speed > 20:
                predicted_intention = "ADVANCE"
                confidence = 0.7
                indicators.append("Movimiento rapido de blindados")
            elif unit_type == "ARTILLERY" and unit.get("deployment_status") == "DEPLOYED":
                predicted_intention = "FIRE_MISSION"
                confidence = 0.8
                indicators.append("Artilleria desplegada")
            elif unit_type == "INFANTRY" and proximity_to_objective < 10:
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

            if heading:
                indicators.append(f"Rumbo {heading} grados")

            analyses.append(IntentionAnalysis(
                unit_id=unit.get("id", str(uuid.uuid4())),
                predicted_intention=predicted_intention,
                confidence=confidence,
                indicators=indicators,
                course_of_action=predicted_intention,
            ))

        return analyses

    async def generate_ctp(self, events: List[Dict[str, Any]]) -> CommonTacticalPicture:
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
        base_threat = {
            "ARMOR": 75.0,
            "INFANTRY": 50.0,
            "ARTILLERY": 85.0,
            "AIR_DEFENSE": 90.0,
            "MISSILE": 95.0,
            "UAV": 60.0,
            "SPECIAL_FORCES": 70.0,
        }.get(entity_type, 30.0)

        strength_mod = event.get("strength", 0.5) * 20
        proximity_mod = max(0, 30 - event.get("distance_to_friendly", 50))
        return min(100.0, base_threat + strength_mod + proximity_mod)

    def _calculate_overall_threat(self, hostiles: List[HostileUnit], friendlies: List[FriendlyUnit]) -> float:
        if not hostiles:
            return 0.0
        total_hostile = sum(h.threat_level * h.strength for h in hostiles)
        total_friendly = sum(f.strength for f in friendlies) if friendlies else 1.0
        ratio = total_hostile / max(total_friendly, 0.1)
        return min(100.0, ratio * 25)

    def _threat_radius(self, entity_type: str, threat_level: float) -> float:
        base_radius = {
            "ARMOR": 15.0,
            "INFANTRY": 5.0,
            "ARTILLERY": 40.0,
            "AIR_DEFENSE": 80.0,
            "MISSILE": 200.0,
            "UAV": 25.0,
            "SPECIAL_FORCES": 10.0,
        }.get(entity_type, 10.0)
        return base_radius * (threat_level / 50.0)

    def _generate_recommendations(
        self,
        hostiles: List[HostileUnit],
        friendlies: List[FriendlyUnit],
        zones: List[ThreatZone],
    ) -> List[Action]:
        actions = []
        high_threats = [h for h in hostiles if h.threat_level > 70]

        if high_threats:
            actions.append(Action(
                action_type="ENGAGE_HIGH_PRIORITY",
                priority=1,
                description=f"Neutralizar {len(high_threats)} amenazas de alta prioridad",
            ))

        if any(z.zone_type == "AIR_DEFENSE_ENGAGEMENT" for z in zones):
            actions.append(Action(
                action_type="SEAD_MISSION",
                priority=1,
                description="Ejecutar mision SEAD contra defensa aerea enemiga",
            ))

        if len(hostiles) > len(friendlies) * 1.5:
            actions.append(Action(
                action_type="REQUEST_REINFORCEMENTS",
                priority=2,
                description="Solicitar refuerzos - superioridad enemiga detectada",
            ))

        if not actions:
            actions.append(Action(
                action_type="MAINTAIN_POSTURE",
                priority=3,
                description="Mantener postura defensiva actual",
            ))

        return actions

    def _determine_relationship(self, e1: Entity, e2: Entity, distance_km: float) -> str:
        if e1.entity_type == e2.entity_type:
            return "SAME_TYPE_FORMATION"
        if distance_km < 2:
            return "DIRECT_SUPPORT"
        if distance_km < 10:
            return "CLOSE_COORDINATION"
        return "AREA_COORDINATION"


jdl_fusion_engine = SituationAssessment()
