import json
import math
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_RULES_DIR = Path(__file__).parent / "rules"

_COMPARATORS = {
    ">=": lambda a, b: a >= b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    "<": lambda a, b: a < b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def _load_rules() -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    if _RULES_DIR.exists():
        for path in sorted(_RULES_DIR.glob("*.json")):
            with open(path, encoding="utf-8") as fp:
                data = json.load(fp)
            rules.extend(data if isinstance(data, list) else [data])
    return rules


def _resolve(event: Dict[str, Any], path: str) -> Any:
    value: Any = event
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _match_condition(value: Any, condition: Any) -> bool:
    if isinstance(condition, bool):
        return value is condition or value == condition
    if isinstance(condition, dict):
        for op, target in condition.items():
            comparator = _COMPARATORS.get(op)
            if comparator is None:
                return False
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False
            if not comparator(value, target):
                return False
        return True
    return value == condition


def _parse_ts(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            return None
    return None


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _position_of(event: Dict[str, Any]) -> Optional[tuple]:
    lat = event.get("lat")
    lon = event.get("lon")
    if lat is None and isinstance(event.get("position"), dict):
        lat = event["position"].get("lat")
        lon = event["position"].get("lon")
    if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
        return float(lat), float(lon)
    return None


class EventCorrelator:
    """
    Correlates events against the declarative rules in ml/rules/*.json and
    applies deterministic spatio-temporal proximity correlation. No simulated
    data: a correlation only fires when every rule condition is satisfied.
    """

    def __init__(self, rules: Optional[List[Dict[str, Any]]] = None):
        self.rules = rules if rules is not None else _load_rules()

    def evaluate_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        matches = []
        for rule in self.rules:
            conditions = rule.get("conditions", {})
            if not conditions:
                continue
            matched = 0
            for key, condition in conditions.items():
                value = _resolve(event, key)
                if value is None:
                    break
                if not _match_condition(value, condition):
                    break
                matched += 1
            if matched == len(conditions):
                entry: Dict[str, Any] = {
                    "id": str(uuid.uuid4()),
                    "rule_id": rule.get("name", "unnamed_rule"),
                    "confidence": round(float(rule.get("weight", 1.0)), 3),
                    "action": rule.get("action"),
                }
                if event.get("event_id"):
                    entry["involved_events"] = [event["event_id"]]
                matches.append(entry)
        return matches

    @staticmethod
    def correlate_multi_domain(
        events: List[Dict[str, Any]],
        max_distance_m: float = 1000.0,
        max_time_delta_s: float = 300.0,
    ) -> List[Dict[str, Any]]:
        correlator = EventCorrelator()
        correlations: List[Dict[str, Any]] = []
        for event in events:
            correlations.extend(correlator.evaluate_event(event))

        rf_events = [e for e in events if e.get("event_type") == "rf_anomaly_event"]
        manual_events = [e for e in events if e.get("event_type") == "manual_observation"]

        for rf in rf_events:
            rf_pos = _position_of(rf)
            rf_ts = _parse_ts(rf.get("ts"))
            if rf_pos is None or rf_ts is None:
                continue
            for man in manual_events:
                if rf.get("asset_id") and rf.get("asset_id") == man.get("asset_id"):
                    continue
                man_pos = _position_of(man)
                man_ts = _parse_ts(man.get("ts"))
                if man_pos is None or man_ts is None:
                    continue
                distance_m = _haversine_m(rf_pos[0], rf_pos[1], man_pos[0], man_pos[1])
                time_delta_s = abs(rf_ts - man_ts)
                if distance_m <= max_distance_m and time_delta_s <= max_time_delta_s:
                    correlations.append({
                        "id": str(uuid.uuid4()),
                        "rule_id": "RF_MANUAL_PROXIMITY",
                        "severity": "HIGH",
                        "description": "RF Anomaly and Manual Observation correlated in close proximity.",
                        "distance_m": round(distance_m, 1),
                        "time_delta_s": round(time_delta_s, 1),
                        "involved_events": [
                            eid for eid in (rf.get("event_id"), man.get("event_id")) if eid
                        ],
                    })

        return correlations
