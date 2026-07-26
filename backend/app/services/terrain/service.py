# -*- coding: utf-8 -*-
import math
import uuid
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

from app.services.terrain.elevation import fetch_elevations

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


class TerrainService:
    DEM_RESOLUTION = 0.001
    MAX_LOS_SAMPLES = 64
    MAX_ROUTE_WAYPOINTS = 25
    GRID_SIZE = 5

    async def line_of_sight(
        self,
        observer: Dict[str, float],
        target: Dict[str, float],
        observer_height_m: float = 2.0,
        target_height_m: float = 2.0,
    ) -> Dict[str, Any]:
        obs = GeoPoint(lat=observer["lat"], lon=observer["lon"])
        tgt = GeoPoint(lat=target["lat"], lon=target["lon"])

        distance_km = _haversine_km(obs, tgt)
        num_samples = min(self.MAX_LOS_SAMPLES, max(10, int(distance_km / self.DEM_RESOLUTION)))

        sample_points = [_intermediate_point(obs, tgt, i / num_samples) for i in range(num_samples + 1)]
        elevations = await fetch_elevations([(p.lat, p.lon) for p in sample_points])

        obs.elevation = float(observer["elevation"]) if "elevation" in observer else elevations[0]
        tgt.elevation = float(target["elevation"]) if "elevation" in target else elevations[-1]

        profile = []
        obstructions = []
        min_clearance = float('inf')
        visible = True

        obs_effective_elev = obs.elevation + observer_height_m
        tgt_effective_elev = tgt.elevation + target_height_m

        for i, point in enumerate(sample_points):
            frac = i / num_samples
            terrain_elev = elevations[i]
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
            "source": "OPEN_ELEVATION_DEM",
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

        num_waypoints = min(self.MAX_ROUTE_WAYPOINTS, max(5, int(_haversine_km(start_pt, end_pt) / 2)))

        endpoints: List[GeoPoint] = []
        for i in range(num_waypoints):
            endpoints.append(_intermediate_point(start_pt, end_pt, i / num_waypoints))
            endpoints.append(_intermediate_point(start_pt, end_pt, (i + 1) / num_waypoints))
        elevations = await fetch_elevations([(p.lat, p.lon) for p in endpoints])

        segments = []
        total_distance = 0.0
        total_cost = 0.0
        obstacles_found = []

        for i in range(num_waypoints):
            seg_start = endpoints[2 * i]
            seg_end = endpoints[2 * i + 1]
            seg_start.elevation = elevations[2 * i]
            seg_end.elevation = elevations[2 * i + 1]

            dist = _haversine_km(seg_start, seg_end)
            elev_diff = seg_end.elevation - seg_start.elevation
            slope = math.degrees(math.atan2(elev_diff, dist * 1000)) if dist > 0 else 0

            avg_elev = (seg_start.elevation + seg_end.elevation) / 2
            terrain_type = self._classify_terrain(avg_elev)
            terrain_cost_factor = self._terrain_cost_factor(terrain_type, vehicle_type)
            slope_factor = 1.0 + abs(slope) / 10.0
            cost = dist * terrain_cost_factor * slope_factor

            seg_obstacles = []
            if abs(slope) > 30:
                seg_obstacles.append(f"Pendiente extrema: {abs(slope):.1f} grados")
            elif abs(slope) > 15:
                seg_obstacles.append(f"Pendiente severa: {abs(slope):.1f} grados")

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
        if any("Pendiente extrema" in o["obstacle"] for o in obstacles_found):
            recommendations.append("Evitar vehiculos con ruedas en pendientes extremas")
        if not recommendations:
            recommendations.append("Ruta transitable - sin obstaculos criticos detectados en el DEM")

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
            "source": "OPEN_ELEVATION_DEM",
        }

    async def _elevation_grid(
        self, center_lat: float, center_lon: float, radius_km: float
    ) -> Tuple[List[Tuple[float, float]], List[float]]:
        n = self.GRID_SIZE
        half = (n - 1) / 2
        step_lat = (radius_km / 111.0) / half if half else 0.0
        cos_lat = max(0.01, math.cos(math.radians(center_lat)))
        step_lon = (radius_km / (111.0 * cos_lat)) / half if half else 0.0
        points = []
        for i in range(n):
            for j in range(n):
                points.append((center_lat + (i - half) * step_lat, center_lon + (j - half) * step_lon))
        elevations = await fetch_elevations(points)
        return points, elevations

    @staticmethod
    def _grid_spacing_m(center_lat: float, radius_km: float, n: int) -> float:
        return (2 * radius_km * 1000) / (n - 1) if n > 1 else 1.0

    def _visible_between(
        self,
        points: List[Tuple[float, float]],
        elevations: List[float],
        idx_a: int,
        idx_b: int,
    ) -> bool:
        n = self.GRID_SIZE
        lat_a, lon_a = points[idx_a]
        lat_b, lon_b = points[idx_b]
        elev_a, elev_b = elevations[idx_a], elevations[idx_b]
        steps = max(2, n * 2)
        for k in range(1, steps):
            frac = k / steps
            lat = lat_a + (lat_b - lat_a) * frac
            lon = lon_a + (lon_b - lon_a) * frac
            gi = min(range(len(points)), key=lambda m: (points[m][0] - lat) ** 2 + (points[m][1] - lon) ** 2)
            line_elev = elev_a + (elev_b - elev_a) * frac
            if elevations[gi] > line_elev:
                return False
        return True

    async def terrain_analysis(
        self,
        area: Dict[str, Any],
    ) -> Dict[str, Any]:
        center_lat = area.get("center_lat", 40.0)
        center_lon = area.get("center_lon", -3.0)
        radius_km = area.get("radius_km", 10.0)

        n = self.GRID_SIZE
        points, elevations = await self._elevation_grid(center_lat, center_lon, radius_km)
        spacing_m = self._grid_spacing_m(center_lat, radius_km, n)

        slopes: List[Tuple[int, int, float]] = []
        for idx in range(len(points)):
            i, j = divmod(idx, n)
            for di, dj in ((1, 0), (0, 1)):
                ni, nj = i + di, j + dj
                if ni >= n or nj >= n:
                    continue
                nidx = ni * n + nj
                slope = math.degrees(math.atan2(elevations[nidx] - elevations[idx], spacing_m))
                slopes.append((idx, nidx, slope))

        abs_slopes = [abs(s[2]) for s in slopes]
        max_slope = max(abs_slopes, default=0.0)

        slope_thresholds = {"INFANTRY": 30.0, "MOTORIZED": 12.0, "ARMOR": 20.0}
        trafficability = {}
        for vehicle, threshold in slope_thresholds.items():
            restricted = [
                {"from": {"lat": points[a][0], "lon": points[a][1]},
                 "to": {"lat": points[b][0], "lon": points[b][1]},
                 "slope_deg": round(abs(s), 1)}
                for a, b, s in slopes if abs(s) > threshold
            ]
            accessible = (1 - len(restricted) / len(slopes)) * 100 if slopes else 100.0
            trafficability[vehicle] = {
                "accessible_pct": round(accessible, 1),
                "slope_threshold_deg": threshold,
                "restricted_zones": restricted,
            }

        ranked = sorted(range(len(points)), key=lambda m: elevations[m], reverse=True)
        mean_elev = sum(elevations) / len(elevations)
        key_terrain = [
            {
                "id": str(uuid.uuid4()),
                "location": {"lat": points[m][0], "lon": points[m][1]},
                "elevation_m": round(elevations[m], 1),
                "strategic_value": "ALTO" if elevations[m] > mean_elev else "MEDIO",
                "description": "Terreno dominante segun DEM",
            }
            for m in ranked[:3]
        ]

        highest = ranked[0]
        dead_ground = []
        visible_count = 0
        for idx in range(len(points)):
            if idx == highest:
                continue
            if self._visible_between(points, elevations, highest, idx):
                visible_count += 1
            else:
                dead_ground.append({
                    "id": str(uuid.uuid4()),
                    "center": {"lat": points[idx][0], "lon": points[idx][1]},
                    "radius_km": round(spacing_m / 2000, 2),
                    "description": "Zona muerta - sin linea de vista desde terreno dominante",
                })

        obstacles = []
        for a, b, s in slopes:
            if abs(s) > 25:
                obstacles.append({
                    "id": str(uuid.uuid4()),
                    "type": "RIDGE",
                    "location": {
                        "lat": (points[a][0] + points[b][0]) / 2,
                        "lon": (points[a][1] + points[b][1]) / 2,
                    },
                    "description": f"Cresta/escarpe detectado en DEM - pendiente {abs(s):.1f} grados",
                    "severity": "ALTA" if abs(s) > 40 else "MEDIA",
                })

        recommendations = []
        if key_terrain:
            recommendations.append("Establecer puesto de observacion en terreno dominante identificado")
        if dead_ground:
            recommendations.append("Instalar repetidor de comunicaciones para zonas muertas detectadas")
        if max_slope > 30:
            recommendations.append("Restringir movimiento de vehiculos en zonas de pendiente severa")
        if not recommendations:
            recommendations.append("Terreno sin restricciones criticas detectadas en el DEM")

        return {
            "analysis_id": str(uuid.uuid4()),
            "area": area,
            "trafficability": trafficability,
            "key_terrain": key_terrain,
            "dead_ground": dead_ground,
            "obstacles": obstacles,
            "coverage_analysis": {
                "los_coverage_pct": round(visible_count / (len(points) - 1) * 100, 1) if len(points) > 1 else 100.0,
                "reference_point": {"lat": points[highest][0], "lon": points[highest][1]},
            },
            "recommendations": recommendations,
            "source": "OPEN_ELEVATION_DEM",
        }

    async def get_elevation(self, lat: float, lon: float) -> Dict[str, Any]:
        elevations = await fetch_elevations([(lat, lon)])
        return {
            "lat": lat,
            "lon": lon,
            "elevation_m": round(elevations[0], 1),
            "source": "OPEN_ELEVATION_DEM",
        }

    async def detect_obstacles(
        self,
        area: Dict[str, Any],
    ) -> Dict[str, Any]:
        center_lat = area.get("center_lat", 40.0)
        center_lon = area.get("center_lon", -3.0)
        radius_km = area.get("radius_km", 10.0)

        n = self.GRID_SIZE
        points, elevations = await self._elevation_grid(center_lat, center_lon, radius_km)
        spacing_m = self._grid_spacing_m(center_lat, radius_km, n)

        obstacles = []
        for idx in range(len(points)):
            i, j = divmod(idx, n)
            for di, dj in ((1, 0), (0, 1)):
                ni, nj = i + di, j + dj
                if ni >= n or nj >= n:
                    continue
                nidx = ni * n + nj
                slope = abs(math.degrees(math.atan2(elevations[nidx] - elevations[idx], spacing_m)))
                if slope > 25:
                    obstacles.append({
                        "obstacle_id": str(uuid.uuid4()),
                        "obstacle_type": "CLIFF" if slope > 45 else "RIDGE",
                        "location": {
                            "lat": (points[idx][0] + points[nidx][0]) / 2,
                            "lon": (points[idx][1] + points[nidx][1]) / 2,
                        },
                        "description": f"Escarpe detectado en DEM - pendiente {slope:.1f} grados",
                        "severity": "ALTA" if slope > 40 else "MEDIA",
                        "bypass_possible": slope <= 45,
                        "dimensions": {"length_m": round(spacing_m, 1)},
                    })

        return {
            "area": area,
            "obstacles": obstacles,
            "total_count": len(obstacles),
            "critical_count": sum(1 for o in obstacles if o["severity"] == "ALTA"),
            "source": "DEM_DERIVED",
        }

    def _classify_terrain(self, elevation: float) -> str:
        if elevation < 50:
            return "LOWLAND"
        elif elevation < 150:
            return "PLAIN"
        elif elevation < 300:
            return "HILLS"
        else:
            return "MOUNTAIN"

    def _terrain_cost_factor(self, terrain_type: str, vehicle_type: str) -> float:
        factors = {
            "PLAIN": {"INFANTRY": 1.0, "MOTORIZED": 1.0, "ARMOR": 1.0, "WHEELED": 1.0, "TRACKED": 1.0},
            "LOWLAND": {"INFANTRY": 1.2, "MOTORIZED": 1.5, "ARMOR": 1.3, "WHEELED": 1.4, "TRACKED": 1.2},
            "HILLS": {"INFANTRY": 2.0, "MOTORIZED": 2.5, "ARMOR": 2.0, "WHEELED": 3.0, "TRACKED": 1.8},
            "MOUNTAIN": {"INFANTRY": 3.5, "MOTORIZED": 4.0, "ARMOR": 5.0, "WHEELED": 5.0, "TRACKED": 3.0},
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
