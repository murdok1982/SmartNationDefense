# -*- coding: utf-8 -*-
import math
import uuid
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class GeoPoint:
    lat: float
    lon: float
    elevation: float = 0.0


@dataclass
class LOSResult:
    visible: bool
    distance_km: float
    min_clearance_m: float
    profile: List[Dict[str, Any]] = field(default_factory=list)
    obstructions: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RouteSegment:
    start: GeoPoint
    end: GeoPoint
    distance_km: float
    slope_deg: float
    terrain_type: str
    cost: float
    obstacles: List[str] = field(default_factory=list)


@dataclass
class RouteAnalysis:
    route_id: str
    segments: List[RouteSegment]
    total_distance_km: float
    estimated_time_min: float
    difficulty: str
    total_cost: float
    terrain_profile: List[Dict[str, Any]] = field(default_factory=list)
    obstacles: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class TerrainAnalysisResult:
    analysis_id: str
    trafficability: Dict[str, Any]
    key_terrain: List[Dict[str, Any]]
    dead_ground: List[Dict[str, Any]]
    obstacles: List[Dict[str, Any]]
    coverage_analysis: Dict[str, Any]
    recommendations: List[str]


@dataclass
class Obstacle:
    obstacle_id: str
    obstacle_type: str
    location: GeoPoint
    dimensions: Dict[str, float]
    severity: str
    bypass_possible: bool
    description: str


def _haversine_km(p1: GeoPoint, p2: GeoPoint) -> float:
    R = 6371.0
    lat1, lon1 = math.radians(p1.lat), math.radians(p1.lon)
    lat2, lon2 = math.radians(p2.lat), math.radians(p2.lon)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _intermediate_point(p1: GeoPoint, p2: GeoPoint, fraction: float) -> GeoPoint:
    lat1, lon1 = math.radians(p1.lat), math.radians(p1.lon)
    lat2, lon2 = math.radians(p2.lat), math.radians(p2.lon)
    d = 2 * math.asin(math.sqrt(
        math.sin((lat1 - lat2) / 2) ** 2 +
        math.cos(lat1) * math.cos(lat2) * math.sin((lon1 - lon2) / 2) ** 2
    ))
    if d == 0:
        return p1
    A = math.sin((1 - fraction) * d) / math.sin(d)
    B = math.sin(fraction * d) / math.sin(d)
    x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
    y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
    z = A * math.sin(lat1) + B * math.sin(lat2)
    lat = math.atan2(z, math.sqrt(x ** 2 + y ** 2))
    lon = math.atan2(y, x)
    return GeoPoint(lat=math.degrees(lat), lon=math.degrees(lon))


def _simulate_elevation(lat: float, lon: float) -> float:
    base = 200.0
    variation = 150 * math.sin(lat * 10) * math.cos(lon * 10)
    noise = 50 * math.sin(lat * 50 + lon * 30)
    return max(0, base + variation + noise)


class TerrainService:
    DEM_RESOLUTION = 0.001

    async def line_of_sight(
        self,
        observer: Dict[str, float],
        target: Dict[str, float],
        observer_height_m: float = 2.0,
        target_height_m: float = 2.0,
    ) -> Dict[str, Any]:
        obs = GeoPoint(
            lat=observer["lat"],
            lon=observer["lon"],
            elevation=observer.get("elevation", _simulate_elevation(observer["lat"], observer["lon"])),
        )
        tgt = GeoPoint(
            lat=target["lat"],
            lon=target["lon"],
            elevation=target.get("elevation", _simulate_elevation(target["lat"], target["lon"])),
        )

        distance_km = _haversine_km(obs, tgt)
        num_samples = max(10, int(distance_km / self.DEM_RESOLUTION))
        profile = []
        obstructions = []
        min_clearance = float('inf')
        visible = True

        obs_effective_elev = obs.elevation + observer_height_m
        tgt_effective_elev = tgt.elevation + target_height_m

        for i in range(num_samples + 1):
            frac = i / num_samples
            point = _intermediate_point(obs, tgt, frac)
            terrain_elev = _simulate_elevation(point.lat, point.lon)
            line_elev = obs_effective_elev + (tgt_effective_elev - obs_effective_elev) * frac

            clearance = line_elev - terrain_elev
            min_clearance = min(min_clearance, clearance)

            profile.append({
                "point": frac,
                "distance_km": round(distance_km * frac, 3),
                "terrain_elevation_m": round(terrain_elev, 1),
                "los_elevation_m": round(line_elev, 1),
                "clearance_m": round(clearance, 1),
            })

            if clearance < 0:
                visible = False
                obstructions.append({
                    "point": frac,
                    "distance_km": round(distance_km * frac, 3),
                    "terrain_elevation_m": round(terrain_elev, 1),
                    "blockage_m": round(abs(clearance), 1),
                })

        return {
            "visible": visible,
            "distance_km": round(distance_km, 3),
            "min_clearance_m": round(min_clearance, 1) if min_clearance != float('inf') else 0,
            "observer": {"lat": obs.lat, "lon": obs.lon, "elevation_m": obs.elevation},
            "target": {"lat": tgt.lat, "lon": tgt.lon, "elevation_m": tgt.elevation},
            "profile": profile,
            "obstructions": obstructions,
        }

    async def route_analysis(
        self,
        start: Dict[str, float],
        end: Dict[str, float],
        vehicle_type: str = "INFANTRY",
        avoid_obstacles: bool = True,
    ) -> Dict[str, Any]:
        start_pt = GeoPoint(lat=start["lat"], lon=start["lon"])
        end_pt = GeoPoint(lat=end["lat"], lon=end["lon"])

        speed_map = {
            "INFANTRY": 4.0,
            "MOTORIZED": 30.0,
            "ARMOR": 20.0,
            "WHEELED": 25.0,
            "TRACKED": 15.0,
        }
        base_speed = speed_map.get(vehicle_type.upper(), 5.0)

        num_waypoints = max(5, int(_haversine_km(start_pt, end_pt) / 2))
        segments = []
        total_distance = 0.0
        total_cost = 0.0
        obstacles_found = []

        for i in range(num_waypoints):
            frac_start = i / num_waypoints
            frac_end = (i + 1) / num_waypoints
            seg_start = _intermediate_point(start_pt, end_pt, frac_start)
            seg_end = _intermediate_point(start_pt, end_pt, frac_end)

            seg_start.elevation = _simulate_elevation(seg_start.lat, seg_start.lon)
            seg_end.elevation = _simulate_elevation(seg_end.lat, seg_end.lon)

            dist = _haversine_km(seg_start, seg_end)
            elev_diff = seg_end.elevation - seg_start.elevation
            slope = math.degrees(math.atan2(elev_diff, dist * 1000)) if dist > 0 else 0

            terrain_type = self._classify_terrain(seg_start, seg_end)
            terrain_cost_factor = self._terrain_cost_factor(terrain_type, vehicle_type)
            slope_factor = 1.0 + abs(slope) / 10.0
            cost = dist * terrain_cost_factor * slope_factor

            seg_obstacles = []
            if terrain_type == "WATER":
                seg_obstacles.append("Cruce de rio requerido")
            if abs(slope) > 30:
                seg_obstacles.append(f"Pendiente extrema: {abs(slope):.1f} grados")
            if terrain_type == "URBAN":
                seg_obstacles.append("Zona urbana - navegacion restringida")

            segment = RouteSegment(
                start=seg_start,
                end=seg_end,
                distance_km=round(dist, 3),
                slope_deg=round(slope, 1),
                terrain_type=terrain_type,
                cost=round(cost, 3),
                obstacles=seg_obstacles,
            )
            segments.append(segment)
            total_distance += dist
            total_cost += cost
            obstacles_found.extend([{"segment": i, "obstacle": o} for o in seg_obstacles])

        estimated_time = (total_distance / base_speed) * 60 if base_speed > 0 else 999
        difficulty = self._classify_difficulty(total_cost, total_distance)

        recommendations = []
        if difficulty == "EXTREME":
            recommendations.append("Ruta extremadamente dificil - considerar alternativas")
        if any("Cruce de rio" in o["obstacle"] for o in obstacles_found):
            recommendations.append("Preparar equipo de cruce de rios")
        if any("Pendiente extrema" in o["obstacle"] for o in obstacles_found):
            recommendations.append("Evitar vehiculos con ruedas en pendientes extremas")
        if not recommendations:
            recommendations.append("Ruta transitable - sin obstaculos criticos")

        return {
            "route_id": str(uuid.uuid4()),
            "segments": [
                {
                    "start": {"lat": s.start.lat, "lon": s.start.lon},
                    "end": {"lat": s.end.lat, "lon": s.end.lon},
                    "distance_km": s.distance_km,
                    "slope_deg": s.slope_deg,
                    "terrain_type": s.terrain_type,
                    "cost": s.cost,
                    "obstacles": s.obstacles,
                }
                for s in segments
            ],
            "total_distance_km": round(total_distance, 3),
            "estimated_time_min": round(estimated_time, 1),
            "difficulty": difficulty,
            "total_cost": round(total_cost, 3),
            "vehicle_type": vehicle_type,
            "obstacles": obstacles_found,
            "recommendations": recommendations,
        }

    async def terrain_analysis(
        self,
        area: Dict[str, Any],
    ) -> Dict[str, Any]:
        center_lat = area.get("center_lat", 40.0)
        center_lon = area.get("center_lon", -3.0)
        radius_km = area.get("radius_km", 10.0)

        trafficability = {
            "INFANTRY": {"accessible_pct": 85, "restricted_zones": []},
            "MOTORIZED": {"accessible_pct": 60, "restricted_zones": []},
            "ARMOR": {"accessible_pct": 45, "restricted_zones": []},
        }

        key_terrain = []
        for i in range(3):
            lat = center_lat + (i - 1) * 0.05
            lon = center_lon + (i - 1) * 0.05
            elev = _simulate_elevation(lat, lon)
            key_terrain.append({
                "id": str(uuid.uuid4()),
                "location": {"lat": lat, "lon": lon},
                "elevation_m": round(elev, 1),
                "strategic_value": "ALTO" if elev > 300 else "MEDIO",
                "description": f"Terreno dominante en sector {i + 1}",
            })

        dead_ground = []
        for i in range(5):
            lat = center_lat + (i * 0.02 - 0.04)
            lon = center_lon + (i * 0.02 - 0.04)
            dead_ground.append({
                "id": str(uuid.uuid4()),
                "center": {"lat": lat, "lon": lon},
                "radius_km": 0.5,
                "description": "Zona muerta - sin cobertura de comunicaciones",
            })

        obstacles = []
        for i in range(2):
            lat = center_lat + (i * 0.03 - 0.015)
            lon = center_lon + (i * 0.03 - 0.015)
            obstacles.append({
                "id": str(uuid.uuid4()),
                "type": "NATURAL" if i == 0 else "ANTROPICO",
                "location": {"lat": lat, "lon": lon},
                "description": "Rio / Zona urbana" if i == 0 else "Zona edificada",
                "severity": "MEDIA",
            })

        return {
            "analysis_id": str(uuid.uuid4()),
            "area": area,
            "trafficability": trafficability,
            "key_terrain": key_terrain,
            "dead_ground": dead_ground,
            "obstacles": obstacles,
            "coverage_analysis": {
                "vhf_coverage_pct": 65,
                "uhf_coverage_pct": 75,
                "los_coverage_pct": 40,
            },
            "recommendations": [
                "Establecer puesto de observacion en terreno dominante",
                "Preparar rutas alternativas evitando zonas restringidas",
                "Instalar repetidor de comunicaciones para zonas muertas",
            ],
        }

    async def get_elevation(self, lat: float, lon: float) -> Dict[str, Any]:
        elevation = _simulate_elevation(lat, lon)
        return {
            "lat": lat,
            "lon": lon,
            "elevation_m": round(elevation, 1),
            "source": "DEM_SIMULATED",
        }

    async def detect_obstacles(
        self,
        area: Dict[str, Any],
    ) -> Dict[str, Any]:
        center_lat = area.get("center_lat", 40.0)
        center_lon = area.get("center_lon", -3.0)
        radius_km = area.get("radius_km", 10.0)

        obstacles = []
        obstacle_configs = [
            ("RIVER", "Rio principal - ancho 50m, caudal medio", "ALTA"),
            ("RIDGE", "Cresta montanosa - elevacion 400m", "MEDIA"),
            ("URBAN", "Zona urbana densa", "MEDIA"),
            ("FOREST", "Bosque denso - visibilidad reducida", "BAJA"),
            ("MARSH", "Pantano - terreno intransitable", "ALTA"),
        ]

        for i, (otype, desc, severity) in enumerate(obstacle_configs):
            lat = center_lat + (i * 0.02 - 0.04)
            lon = center_lon + (i * 0.015 - 0.03)
            obstacles.append({
                "obstacle_id": str(uuid.uuid4()),
                "obstacle_type": otype,
                "location": {"lat": lat, "lon": lon},
                "description": desc,
                "severity": severity,
                "bypass_possible": otype not in ("MARSH",),
                "dimensions": {"width_m": 50 + i * 20, "length_m": 200 + i * 100},
            })

        return {
            "area": area,
            "obstacles": obstacles,
            "total_count": len(obstacles),
            "critical_count": sum(1 for o in obstacles if o["severity"] == "ALTA"),
        }

    def _classify_terrain(self, p1: GeoPoint, p2: GeoPoint) -> str:
        avg_lat = (p1.lat + p2.lat) / 2
        avg_lon = (p1.lon + p2.lon) / 2
        elev = _simulate_elevation(avg_lat, avg_lon)
        if elev < 50:
            return "LOWLAND"
        elif elev < 150:
            return "PLAIN"
        elif elev < 300:
            return "HILLS"
        else:
            hash_val = int(abs(avg_lat * 1000 + avg_lon * 1000)) % 5
            if hash_val == 0:
                return "WATER"
            elif hash_val == 1:
                return "URBAN"
            elif hash_val == 2:
                return "FOREST"
            else:
                return "MOUNTAIN"

    def _terrain_cost_factor(self, terrain_type: str, vehicle_type: str) -> float:
        factors = {
            "PLAIN": {"INFANTRY": 1.0, "MOTORIZED": 1.0, "ARMOR": 1.0, "WHEELED": 1.0, "TRACKED": 1.0},
            "LOWLAND": {"INFANTRY": 1.2, "MOTORIZED": 1.5, "ARMOR": 1.3, "WHEELED": 1.4, "TRACKED": 1.2},
            "HILLS": {"INFANTRY": 2.0, "MOTORIZED": 2.5, "ARMOR": 2.0, "WHEELED": 3.0, "TRACKED": 1.8},
            "MOUNTAIN": {"INFANTRY": 3.5, "MOTORIZED": 4.0, "ARMOR": 5.0, "WHEELED": 5.0, "TRACKED": 3.0},
            "FOREST": {"INFANTRY": 1.8, "MOTORIZED": 2.0, "ARMOR": 2.5, "WHEELED": 2.5, "TRACKED": 2.0},
            "WATER": {"INFANTRY": 10.0, "MOTORIZED": 10.0, "ARMOR": 10.0, "WHEELED": 10.0, "TRACKED": 10.0},
            "URBAN": {"INFANTRY": 2.0, "MOTORIZED": 1.5, "ARMOR": 3.0, "WHEELED": 1.8, "TRACKED": 2.5},
        }
        return factors.get(terrain_type, {}).get(vehicle_type.upper(), 2.0)

    def _classify_difficulty(self, total_cost: float, total_distance: float) -> str:
        if total_distance == 0:
            return "EASY"
        ratio = total_cost / total_distance
        if ratio < 1.5:
            return "EASY"
        elif ratio < 2.5:
            return "MODERATE"
        elif ratio < 4.0:
            return "DIFFICULT"
        else:
            return "EXTREME"


terrain_service = TerrainService()
