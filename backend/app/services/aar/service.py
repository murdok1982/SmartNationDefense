# -*- coding: utf-8 -*-
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class AARService:
    def __init__(self):
        self._reviews: Dict[str, Dict[str, Any]] = {}

    async def create_aar(self, aar_data: Dict[str, Any]) -> Dict[str, Any]:
        aar_id = str(uuid.uuid4())
        aar = {
            "id": aar_id,
            "operation_id": aar_data.get("operation_id", ""),
            "operation_name": aar_data.get("operation_name", ""),
            "start_time": aar_data.get("start_time", datetime.now(timezone.utc).isoformat()),
            "end_time": aar_data.get("end_time"),
            "participants": aar_data.get("participants", []),
            "timeline": [],
            "objectives": aar_data.get("objectives", []),
            "outcomes": [],
            "lessons_learned": [],
            "recommendations": [],
            "performance_metrics": aar_data.get("performance_metrics", {}),
            "status": "IN_PROGRESS",
            "classification": aar_data.get("classification", "CONFIDENTIAL"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": aar_data.get("created_by", "SYSTEM"),
        }
        self._reviews[aar_id] = aar
        return aar

    async def get_aar(self, aar_id: str) -> Optional[Dict[str, Any]]:
        return self._reviews.get(aar_id)

    async def add_timeline_event(self, aar_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        aar = self._reviews.get(aar_id)
        if not aar:
            raise ValueError(f"AAR {aar_id} no encontrada")

        event = {
            "id": str(uuid.uuid4()),
            "timestamp": event_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "event_type": event_data.get("event_type", "ACTION"),
            "description": event_data.get("description", ""),
            "actor": event_data.get("actor", ""),
            "location": event_data.get("location", {}),
            "outcome": event_data.get("outcome", ""),
            "significance": event_data.get("significance", "NORMAL"),
        }
        aar["timeline"].append(event)
        aar["timeline"].sort(key=lambda e: e["timestamp"])
        return event

    async def add_lesson_learned(self, aar_id: str, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        aar = self._reviews.get(aar_id)
        if not aar:
            raise ValueError(f"AAR {aar_id} no encontrada")

        lesson = {
            "id": str(uuid.uuid4()),
            "category": lesson_data.get("category", "TACTICAL"),
            "observation": lesson_data.get("observation", ""),
            "discussion": lesson_data.get("discussion", ""),
            "recommendation": lesson_data.get("recommendation", ""),
            "priority": lesson_data.get("priority", "MEDIUM"),
            "sustains": lesson_data.get("sustains", True),
            "improves": lesson_data.get("improves", False),
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        aar["lessons_learned"].append(lesson)
        return lesson

    async def get_replay(self, aar_id: str) -> Dict[str, Any]:
        aar = self._reviews.get(aar_id)
        if not aar:
            raise ValueError(f"AAR {aar_id} no encontrada")

        replay_events = []
        for event in aar.get("timeline", []):
            replay_events.append({
                "timestamp": event["timestamp"],
                "type": event["event_type"],
                "description": event["description"],
                "actor": event.get("actor", ""),
                "location": event.get("location", {}),
                "visual_data": {
                    "icon": self._get_event_icon(event["event_type"]),
                    "color": self._get_event_color(event.get("significance", "NORMAL")),
                },
            })

        return {
            "aar_id": aar_id,
            "operation_name": aar["operation_name"],
            "start_time": aar["start_time"],
            "end_time": aar.get("end_time"),
            "total_events": len(replay_events),
            "events": replay_events,
            "participants": aar.get("participants", []),
            "duration_minutes": self._calculate_duration(aar["start_time"], aar.get("end_time")),
        }

    async def finalize_aar(self, aar_id: str, finalize_data: Dict[str, Any]) -> Dict[str, Any]:
        aar = self._reviews.get(aar_id)
        if not aar:
            raise ValueError(f"AAR {aar_id} no encontrada")

        aar["end_time"] = finalize_data.get("end_time", datetime.now(timezone.utc).isoformat())
        aar["outcomes"] = finalize_data.get("outcomes", [])
        aar["recommendations"] = finalize_data.get("recommendations", aar.get("recommendations", []))
        aar["performance_metrics"] = finalize_data.get("performance_metrics", aar.get("performance_metrics", {}))
        aar["status"] = "FINALIZED"
        aar["finalized_at"] = datetime.now(timezone.utc).isoformat()

        aar["summary"] = self._generate_summary(aar)
        return aar

    def _get_event_icon(self, event_type: str) -> str:
        icons = {
            "MOVEMENT": "arrow-right",
            "ENGAGEMENT": "crosshair",
            "COMMUNICATION": "radio",
            "LOGISTICS": "truck",
            "MEDICAL": "plus-circle",
            "ACTION": "circle",
            "DECISION": "flag",
            "DISCOVERY": "search",
        }
        return icons.get(event_type, "circle")

    def _get_event_color(self, significance: str) -> str:
        colors = {
            "CRITICAL": "#ff0000",
            "HIGH": "#ff8800",
            "NORMAL": "#0088ff",
            "LOW": "#00cc00",
        }
        return colors.get(significance, "#888888")

    def _calculate_duration(self, start: str, end: Optional[str]) -> float:
        try:
            start_dt = datetime.fromisoformat(start)
            if end:
                end_dt = datetime.fromisoformat(end)
            else:
                end_dt = datetime.now(timezone.utc)
            return (end_dt - start_dt).total_seconds() / 60
        except Exception:
            return 0.0

    def _generate_summary(self, aar: Dict[str, Any]) -> Dict[str, Any]:
        objectives = aar.get("objectives", [])
        outcomes = aar.get("outcomes", [])
        lessons = aar.get("lessons_learned", [])

        objectives_met = sum(1 for o in objectives if o.get("status") == "ACHIEVED")
        total_objectives = len(objectives)

        return {
            "operation_name": aar["operation_name"],
            "duration_minutes": self._calculate_duration(aar["start_time"], aar.get("end_time")),
            "total_participants": len(aar.get("participants", [])),
            "total_timeline_events": len(aar.get("timeline", [])),
            "objectives_achieved": objectives_met,
            "objectives_total": total_objectives,
            "success_rate": round(objectives_met / max(total_objectives, 1) * 100, 1),
            "lessons_count": len(lessons),
            "critical_lessons": sum(1 for l in lessons if l.get("priority") == "HIGH"),
        }


aar_service = AARService()
