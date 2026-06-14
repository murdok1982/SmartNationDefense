# -*- coding: utf-8 -*-
import math
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class TacticalMapService:
    LAYER_TYPES = {
        "SATELLITE": {"name": "Imagen Satelital", "z_index": 1, "default_visible": True},
        "TERRAIN": {"name": "Modelo de Terreno 3D", "z_index": 2, "default_visible": True},
        "TACTICAL": {"name": "Simbolos Tacticos", "z_index": 3, "default_visible": True},
        "THREAT": {"name": "Zonas de Amenaza", "z_index": 4, "default_visible": False},
        "COMMUNICATIONS": {"name": "Cobertura Comunicaciones", "z_index": 5, "default_visible": False},
        "ENGAGEMENT": {"name": "Zonas de Engagement", "z_index": 6, "default_visible": False},
        "WEATHER": {"name": "Condiciones Meteorologicas", "z_index": 7, "default_visible": False},
        "LOGISTICS": {"name": "Rutas Logisticas", "z_index": 8, "default_visible": False},
        "OBSTACLES": {"name": "Obstaculos", "z_index": 9, "default_visible": True},
        "BOUNDARIES": {"name": "Limites de Unidad", "z_index": 10, "default_visible": True},
    }

    def __init__(self):
        self._overlays: Dict[str, Dict[str, Any]] = {}
        self._unit_history: Dict[str, List[Dict[str, Any]]] = {}
        self._active_layers: Dict[str, bool] = {k: v["default_visible"] for k, v in self.LAYER_TYPES.items()}

    async def get_layers(self) -> List[Dict[str, Any]]:
        layers = []
        for layer_id, config in self.LAYER_TYPES.items():
            layers.append({
                "id": layer_id,
                "name": config["name"],
                "z_index": config["z_index"],
                "visible": self._active_layers.get(layer_id, False),
                "type": layer_id,
            })
        layers.sort(key=lambda l: l["z_index"])
        return layers

    async def toggle_layer(self, layer_id: str, visible: bool) -> Dict[str, Any]:
        if layer_id not in self.LAYER_TYPES:
            raise ValueError(f"Capa invalida: {layer_id}")
        self._active_layers[layer_id] = visible
        return {"layer_id": layer_id, "visible": visible}

    async def add_overlay(self, overlay_data: Dict[str, Any]) -> Dict[str, Any]:
        overlay_id = str(uuid.uuid4())
        overlay = {
            "id": overlay_id,
            "name": overlay_data.get("name", ""),
            "layer_type": overlay_data.get("layer_type", "TACTICAL"),
            "geojson": overlay_data.get("geojson", {}),
            "style": overlay_data.get("style", {}),
            "visible": overlay_data.get("visible", True),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": overlay_data.get("created_by", "SYSTEM"),
            "metadata": overlay_data.get("metadata", {}),
        }
        self._overlays[overlay_id] = overlay
        return overlay

    async def remove_overlay(self, overlay_id: str) -> bool:
        if overlay_id in self._overlays:
            del self._overlays[overlay_id]
            return True
        return False

    async def get_overlays(self, layer_type: Optional[str] = None) -> List[Dict[str, Any]]:
        results = []
        for o in self._overlays.values():
            if layer_type and o.get("layer_type") != layer_type:
                continue
            results.append(o)
        return results

    async def track_unit(self, unit_data: Dict[str, Any]) -> Dict[str, Any]:
        unit_id = unit_data.get("unit_id", "")
        if unit_id not in self._unit_history:
            self._unit_history[unit_id] = []

        position = {
            "lat": unit_data.get("lat", 0.0),
            "lon": unit_data.get("lon", 0.0),
            "altitude": unit_data.get("altitude", 0.0),
            "heading": unit_data.get("heading", 0.0),
            "speed": unit_data.get("speed", 0.0),
            "status": unit_data.get("status", "ACTIVE"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._unit_history[unit_id].append(position)
        return position

    async def get_unit_history(
        self,
        unit_id: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        history = self._unit_history.get(unit_id, [])

        if start_time:
            history = [h for h in history if h["timestamp"] >= start_time]
        if end_time:
            history = [h for h in history if h["timestamp"] <= end_time]

        history = history[-limit:]

        path_points = [{"lat": h["lat"], "lon": h["lon"]} for h in history]
        geojson_line = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[p["lon"], p["lat"]] for p in path_points],
            },
            "properties": {"unit_id": unit_id},
        }

        return {
            "unit_id": unit_id,
            "positions": history,
            "total_positions": len(history),
            "path_geojson": geojson_line,
            "first_seen": history[0]["timestamp"] if history else None,
            "last_seen": history[-1]["timestamp"] if history else None,
        }

    async def calculate_engagement_zone(
        self,
        unit_location: Dict[str, float],
        weapon_system: str = "INFANTRY",
    ) -> Dict[str, Any]:
        weapon_ranges = {
            "INFANTRY": {"min_range_km": 0, "max_range_km": 0.5, "effective_km": 0.3},
            "MACHINEGUN": {"min_range_km": 0, "max_range_km": 1.5, "effective_km": 1.0},
            "ANTITANK": {"min_range_km": 0.1, "max_range_km": 4.0, "effective_km": 2.5},
            "ARTILLERY_120MM": {"min_range_km": 1.0, "max_range_km": 18.0, "effective_km": 15.0},
            "ARTILLERY_155MM": {"min_range_km": 3.0, "max_range_km": 40.0, "effective_km": 30.0},
            "SAM_SHORT": {"min_range_km": 0.5, "max_range_km": 15.0, "effective_km": 12.0},
            "SAM_LONG": {"min_range_km": 5.0, "max_range_km": 100.0, "effective_km": 80.0},
            "ANTI_SHIP": {"min_range_km": 5.0, "max_range_km": 200.0, "effective_km": 150.0},
        }

        weapon = weapon_ranges.get(weapon_system.upper(), weapon_ranges["INFANTRY"])
        lat = unit_location.get("lat", 0.0)
        lon = unit_location.get("lon", 0.0)

        max_range = self._generate_circle(lat, lon, weapon["max_range_km"], 36)
        effective_range = self._generate_circle(lat, lon, weapon["effective_km"], 36)

        zone_geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [max_range],
                    },
                    "properties": {
                        "zone_type": "MAX_RANGE",
                        "weapon_system": weapon_system,
                        "range_km": weapon["max_range_km"],
                        "fill_color": "rgba(255,0,0,0.1)",
                        "stroke_color": "rgba(255,0,0,0.5)",
                    },
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [effective_range],
                    },
                    "properties": {
                        "zone_type": "EFFECTIVE_RANGE",
                        "weapon_system": weapon_system,
                        "range_km": weapon["effective_km"],
                        "fill_color": "rgba(255,165,0,0.2)",
                        "stroke_color": "rgba(255,165,0,0.7)",
                    },
                },
            ],
        }

        return {
            "weapon_system": weapon_system,
            "unit_location": unit_location,
            "max_range_km": weapon["max_range_km"],
            "effective_range_km": weapon["effective_km"],
            "min_range_km": weapon["min_range_km"],
            "zone_geojson": zone_geojson,
        }

    async def calculate_comm_range(
        self,
        transmitter_location: Dict[str, float],
        comm_system: str = "VHF",
        terrain_factor: float = 0.7,
    ) -> Dict[str, Any]:
        comm_ranges = {
            "VHF": {"base_range_km": 30, "frequency": "30-88 MHz"},
            "UHF": {"base_range_km": 20, "frequency": "225-400 MHz"},
            "HF": {"base_range_km": 500, "frequency": "2-30 MHz"},
            "SATCOM": {"base_range_km": 2000, "frequency": "GHz"},
            "TACTICAL_DATA": {"base_range_km": 15, "frequency": "UHF"},
        }

        comm = comm_ranges.get(comm_system.upper(), comm_ranges["VHF"])
        effective_range = comm["base_range_km"] * terrain_factor

        lat = transmitter_location.get("lat", 0.0)
        lon = transmitter_location.get("lon", 0.0)
        circle = self._generate_circle(lat, lon, effective_range, 36)

        coverage_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [circle],
            },
            "properties": {
                "comm_system": comm_system,
                "base_range_km": comm["base_range_km"],
                "effective_range_km": round(effective_range, 1),
                "terrain_factor": terrain_factor,
                "frequency": comm["frequency"],
                "fill_color": "rgba(0,100,255,0.15)",
                "stroke_color": "rgba(0,100,255,0.5)",
            },
        }

        return {
            "comm_system": comm_system,
            "transmitter_location": transmitter_location,
            "base_range_km": comm["base_range_km"],
            "effective_range_km": round(effective_range, 1),
            "terrain_factor": terrain_factor,
            "coverage_geojson": coverage_geojson,
        }

    async def get_map_state(self) -> Dict[str, Any]:
        return {
            "layers": await self.get_layers(),
            "overlays": await self.get_overlays(),
            "tracked_units": len(self._unit_history),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_circle(self, center_lat: float, center_lon: float, radius_km: float, points: int) -> List[List[float]]:
        coords = []
        for i in range(points + 1):
            angle = 2 * math.pi * i / points
            dlat = (radius_km / 111.0) * math.cos(angle)
            dlon = (radius_km / (111.0 * math.cos(math.radians(center_lat)))) * math.sin(angle)
            coords.append([round(center_lon + dlon, 6), round(center_lat + dlat, 6)])
        return coords


tactical_map_service = TacticalMapService()
