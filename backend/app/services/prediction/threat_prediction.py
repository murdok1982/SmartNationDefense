# -*- coding: utf-8 -*-
import math
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Location:
    lat: float
    lon: float


@dataclass
class ThreatPrediction:
    enemy_unit_id: str
    current_location: Location
    predicted_location: Location
    confidence: float
    time_horizon_min: int
    movement_pattern: str
    threat_level: float
    recommended_action: str
    trajectory_points: List[Location] = field(default_factory=list)
    anomaly_score: float = 0.0


class KalmanFilter:
    def __init__(self, process_noise: float = 0.1, measurement_noise: float = 1.0):
        self.q = process_noise
        self.r = measurement_noise
        self.x = [0.0, 0.0, 0.0, 0.0]
        self.P = [[1000, 0, 0, 0], [0, 1000, 0, 0], [0, 0, 1000, 0], [0, 0, 0, 1000]]
        self.F = [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]]
        self.H = [[1, 0, 0, 0], [0, 1, 0, 0]]
        self.initialized = False

    def initialize(self, lat: float, lon: float):
        self.x = [lat, lon, 0.0, 0.0]
        self.initialized = True

    def predict(self) -> Tuple[float, float]:
        if not self.initialized:
            return 0.0, 0.0
        x_new = [
            self.F[0][0] * self.x[0] + self.F[0][1] * self.x[1] + self.F[0][2] * self.x[2] + self.F[0][3] * self.x[3],
            self.F[1][0] * self.x[0] + self.F[1][1] * self.x[1] + self.F[1][2] * self.x[2] + self.F[1][3] * self.x[3],
            self.F[2][0] * self.x[0] + self.F[2][1] * self.x[1] + self.F[2][2] * self.x[2] + self.F[2][3] * self.x[3],
            self.F[3][0] * self.x[0] + self.F[3][1] * self.x[1] + self.F[3][2] * self.x[2] + self.F[3][3] * self.x[3],
        ]
        self.x = x_new
        return self.x[0], self.x[1]

    def update(self, lat: float, lon: float) -> Tuple[float, float]:
        if not self.initialized:
            self.initialize(lat, lon)
            return lat, lon
        y = [lat - self.x[0], lon - self.x[1]]
        S11 = self.P[0][0] + self.r
        S12 = self.P[0][1]
        S21 = self.P[1][0]
        S22 = self.P[1][1] + self.r
        det = S11 * S22 - S12 * S21
        if abs(det) < 1e-10:
            det = 1e-10
        K00 = (self.P[0][0] * S22 - self.P[0][1] * S21) / det
        K01 = (self.P[0][1] * S11 - self.P[0][0] * S12) / det
        K10 = (self.P[1][0] * S22 - self.P[1][1] * S21) / det
        K11 = (self.P[1][1] * S11 - self.P[1][0] * S12) / det
        K20 = (self.P[2][0] * S22 - self.P[2][1] * S21) / det
        K21 = (self.P[2][1] * S11 - self.P[2][0] * S12) / det
        K30 = (self.P[3][0] * S22 - self.P[3][1] * S21) / det
        K31 = (self.P[3][1] * S11 - self.P[3][0] * S12) / det

        self.x[0] += K00 * y[0] + K01 * y[1]
        self.x[1] += K10 * y[0] + K11 * y[1]
        self.x[2] += K20 * y[0] + K21 * y[1]
        self.x[3] += K30 * y[0] + K31 * y[1]
        return self.x[0], self.x[1]


class ThreatPredictionService:
    def __init__(self):
        self._kalman_filters: Dict[str, KalmanFilter] = {}
        self._history: Dict[str, List[Dict[str, Any]]] = {}
        self._patterns: Dict[str, str] = {}

    async def predict_movement(
        self,
        unit_data: Dict[str, Any],
        time_horizon_min: int = 60,
    ) -> Dict[str, Any]:
        unit_id = unit_data.get("id", str(uuid.uuid4()))
        current_lat = unit_data.get("lat", 0.0)
        current_lon = unit_data.get("lon", 0.0)

        if unit_id not in self._history:
            self._history[unit_id] = []
        self._history[unit_id].append({
            "lat": current_lat,
            "lon": current_lon,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "speed": unit_data.get("speed", 0),
            "heading": unit_data.get("heading", 0),
        })

        if unit_id not in self._kalman_filters:
            self._kalman_filters[unit_id] = KalmanFilter()

        kf = self._kalman_filters[unit_id]
        kf.update(current_lat, current_lon)

        trajectory = []
        pred_lat, pred_lon = current_lat, current_lon
        steps = max(1, time_horizon_min // 5)
        for _ in range(steps):
            pred_lat, pred_lon = kf.predict()
            trajectory.append({"lat": round(pred_lat, 6), "lon": round(pred_lon, 6)})

        if trajectory:
            final = trajectory[-1]
            predicted_lat, predicted_lon = final["lat"], final["lon"]
        else:
            predicted_lat, predicted_lon = current_lat, current_lon

        pattern = self._detect_pattern(unit_id)
        confidence = self._calculate_confidence(unit_id)
        anomaly_score = self._detect_anomaly(unit_id, current_lat, current_lon)
        threat_level = self._assess_threat_level(unit_data, anomaly_score)
        recommended = self._recommend_action(threat_level, pattern)

        prediction = {
            "prediction_id": str(uuid.uuid4()),
            "enemy_unit_id": unit_id,
            "current_location": {"lat": current_lat, "lon": current_lon},
            "predicted_location": {"lat": round(predicted_lat, 6), "lon": round(predicted_lon, 6)},
            "confidence": round(confidence, 3),
            "time_horizon_min": time_horizon_min,
            "movement_pattern": pattern,
            "threat_level": round(threat_level, 1),
            "recommended_action": recommended,
            "trajectory_points": trajectory,
            "anomaly_score": round(anomaly_score, 3),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return prediction

    async def detect_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        anomalies = []
        for event in events:
            unit_id = event.get("id", "")
            lat = event.get("lat", 0.0)
            lon = event.get("lon", 0.0)

            if unit_id in self._history and len(self._history[unit_id]) >= 3:
                score = self._detect_anomaly(unit_id, lat, lon)
                if score > 0.7:
                    anomalies.append({
                        "unit_id": unit_id,
                        "location": {"lat": lat, "lon": lon},
                        "anomaly_score": round(score, 3),
                        "anomaly_type": self._classify_anomaly(unit_id, lat, lon),
                        "description": f"Comportamiento anomalo detectado en unidad {unit_id}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        return anomalies

    async def analyze_pattern_of_life(self, unit_id: str) -> Dict[str, Any]:
        history = self._history.get(unit_id, [])
        if len(history) < 5:
            return {
                "unit_id": unit_id,
                "status": "INSUFFICIENT_DATA",
                "message": "Se necesitan al menos 5 observaciones",
            }

        locations = [(h["lat"], h["lon"]) for h in history]
        center_lat = sum(l[0] for l in locations) / len(locations)
        center_lon = sum(l[1] for l in locations) / len(locations)

        max_radius = 0
        for lat, lon in locations:
            d = math.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2) * 111
            max_radius = max(max_radius, d)

        speeds = [h.get("speed", 0) for h in history if h.get("speed", 0) > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0

        pattern = self._detect_pattern(unit_id)

        return {
            "unit_id": unit_id,
            "status": "ANALYZED",
            "observations": len(history),
            "pattern_of_life": pattern,
            "area_of_operations": {
                "center": {"lat": round(center_lat, 6), "lon": round(center_lon, 6)},
                "radius_km": round(max_radius, 2),
            },
            "movement_stats": {
                "avg_speed_kmh": round(avg_speed, 1),
                "max_speed_kmh": round(max(speeds, default=0), 1),
                "total_observations": len(history),
            },
            "routine_detected": pattern in ("PATROL", "GARRISON", "LOGISTICS"),
            "predictability": round(self._calculate_confidence(unit_id), 3),
        }

    async def early_warning(
        self,
        friendly_locations: List[Dict[str, float]],
        threat_radius_km: float = 50.0,
    ) -> List[Dict[str, Any]]:
        warnings = []
        for unit_id, kf in self._kalman_filters.items():
            if not kf.initialized:
                continue
            pred_lat, pred_lon = kf.predict()
            for friendly in friendly_locations:
                dist = math.sqrt(
                    (pred_lat - friendly["lat"]) ** 2 + (pred_lon - friendly["lon"]) ** 2
                ) * 111
                if dist < threat_radius_km:
                    history = self._history.get(unit_id, [])
                    threat_level = 70.0 if dist < threat_radius_km / 2 else 40.0
                    warnings.append({
                        "warning_id": str(uuid.uuid4()),
                        "threat_unit_id": unit_id,
                        "threat_location": {"lat": pred_lat, "lon": pred_lon},
                        "friendly_location": friendly,
                        "distance_km": round(dist, 2),
                        "threat_level": threat_level,
                        "estimated_time_min": round(dist / 30 * 60, 1),
                        "recommended_action": "ALERT" if dist < threat_radius_km / 2 else "MONITOR",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
        warnings.sort(key=lambda w: w["distance_km"])
        return warnings

    def _detect_pattern(self, unit_id: str) -> str:
        history = self._history.get(unit_id, [])
        if len(history) < 3:
            return "UNKNOWN"

        speeds = [h.get("speed", 0) for h in history[-5:]]
        headings = [h.get("heading", 0) for h in history[-5:]]

        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        heading_variance = self._circular_variance(headings)

        if avg_speed < 2 and heading_variance > 2:
            return "GARRISON"
        elif avg_speed > 20 and heading_variance < 0.5:
            return "RAPID_ADVANCE"
        elif avg_speed > 5 and heading_variance < 1:
            return "ADVANCE"
        elif avg_speed > 5 and heading_variance > 2:
            return "PATROL"
        elif avg_speed > 0 and len(history) > 10:
            locs = [(h["lat"], h["lon"]) for h in history]
            if self._is_circular_pattern(locs):
                return "PATROL"
        return "MANEUVER"

    def _calculate_confidence(self, unit_id: str) -> float:
        history = self._history.get(unit_id, [])
        if len(history) < 3:
            return 0.2
        n = len(history)
        base = min(0.5, n * 0.05)
        pattern = self._detect_pattern(unit_id)
        pattern_bonus = {"GARRISON": 0.3, "PATROL": 0.25, "ADVANCE": 0.2, "RAPID_ADVANCE": 0.15}.get(pattern, 0.1)
        return min(0.95, base + pattern_bonus)

    def _detect_anomaly(self, unit_id: str, lat: float, lon: float) -> float:
        history = self._history.get(unit_id, [])
        if len(history) < 5:
            return 0.0

        past_locs = [(h["lat"], h["lon"]) for h in history[-10:]]
        center_lat = sum(l[0] for l in past_locs) / len(past_locs)
        center_lon = sum(l[1] for l in past_locs) / len(past_locs)

        distances = [math.sqrt((l[0] - center_lat) ** 2 + (l[1] - center_lon) ** 2) * 111 for l in past_locs]
        avg_dist = sum(distances) / len(distances)
        current_dist = math.sqrt((lat - center_lat) ** 2 + (lon - center_lon) ** 2) * 111

        if avg_dist == 0:
            return 0.0
        deviation = abs(current_dist - avg_dist) / max(avg_dist, 1)
        return min(1.0, deviation)

    def _classify_anomaly(self, unit_id: str, lat: float, lon: float) -> str:
        history = self._history.get(unit_id, [])
        if not history:
            return "UNKNOWN"
        last = history[-1]
        dist = math.sqrt((lat - last["lat"]) ** 2 + (lon - last["lon"]) ** 2) * 111
        if dist > 100:
            return "TELEPORTATION"
        speeds = [h.get("speed", 0) for h in history[-5:]]
        if speeds and max(speeds) > 0:
            implied_speed = dist / max((datetime.now(timezone.utc) - datetime.fromisoformat(last["timestamp"])).total_seconds() / 3600, 0.01)
            if implied_speed > max(speeds) * 3:
                return "SPEED_ANOMALY"
        return "POSITION_ANOMALY"

    def _assess_threat_level(self, unit_data: Dict[str, Any], anomaly_score: float) -> float:
        base = unit_data.get("threat_level", 50.0)
        anomaly_mod = anomaly_score * 20
        speed = unit_data.get("speed", 0)
        speed_mod = min(20, speed / 2)
        return min(100.0, base + anomaly_mod + speed_mod)

    def _recommend_action(self, threat_level: float, pattern: str) -> str:
        if threat_level > 80:
            return "ENGAGE_IMMEDIATELY"
        elif threat_level > 60:
            return "HIGH_ALERT"
        elif threat_level > 40:
            return "INCREASE_SURVEILLANCE"
        else:
            return "CONTINUE_MONITORING"

    def _circular_variance(self, headings: List[float]) -> float:
        if not headings:
            return 0.0
        sin_sum = sum(math.sin(math.radians(h)) for h in headings)
        cos_sum = sum(math.cos(math.radians(h)) for h in headings)
        n = len(headings)
        R = math.sqrt(sin_sum ** 2 + cos_sum ** 2) / n
        return 1 - R

    def _is_circular_pattern(self, locations: List[Tuple[float, float]]) -> bool:
        if len(locations) < 5:
            return False
        center_lat = sum(l[0] for l in locations) / len(locations)
        center_lon = sum(l[1] for l in locations) / len(locations)
        distances = [math.sqrt((l[0] - center_lat) ** 2 + (l[1] - center_lon) ** 2) for l in locations]
        avg_dist = sum(distances) / len(distances)
        if avg_dist == 0:
            return False
        variance = sum((d - avg_dist) ** 2 for d in distances) / len(distances)
        cv = math.sqrt(variance) / avg_dist
        return cv < 0.3


threat_prediction_service = ThreatPredictionService()
