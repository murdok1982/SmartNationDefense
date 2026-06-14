# -*- coding: utf-8 -*-
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class LogisticsService:
    SUPPLY_TYPES = {"AMMO", "FUEL", "RATION", "MEDICAL", "EQUIPMENT", "WATER", "COMMS"}
    PERSONNEL_STATUS = {"ACTIVE", "WIA", "KIA", "MIA", "OFF_DUTY", "RESERVE"}
    MEDEVAC_URGENCY = {"URGENT": 1, "PRIORITY": 2, "ROUTINE": 3}

    def __init__(self):
        self._supplies: Dict[str, Dict[str, Any]] = {}
        self._requests: Dict[str, Dict[str, Any]] = {}
        self._personnel: Dict[str, Dict[str, Any]] = {}
        self._medevacs: Dict[str, Dict[str, Any]] = {}
        self._maintenance: Dict[str, Dict[str, Any]] = {}

    async def get_supplies(
        self,
        supply_type: Optional[str] = None,
        location_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results = []
        for s in self._supplies.values():
            if supply_type and s.get("supply_type") != supply_type:
                continue
            if location_id and s.get("location_id") != location_id:
                continue
            if status and s.get("status") != status:
                continue
            results.append(s)
        return results

    async def add_supply(self, supply_data: Dict[str, Any]) -> Dict[str, Any]:
        supply_id = str(uuid.uuid4())
        supply = {
            "id": supply_id,
            "supply_type": supply_data.get("supply_type", "AMMO"),
            "quantity": supply_data.get("quantity", 0),
            "unit": supply_data.get("unit", "UNITS"),
            "location_id": supply_data.get("location_id"),
            "location": supply_data.get("location", {}),
            "status": "AVAILABLE",
            "priority": supply_data.get("priority", "MEDIUM"),
            "min_threshold": supply_data.get("min_threshold", 0),
            "classification": supply_data.get("classification", "CONFIDENTIAL"),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self._supplies[supply_id] = supply
        return supply

    async def request_supply(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        request = {
            "id": request_id,
            "supply_type": request_data.get("supply_type", "AMMO"),
            "quantity": request_data.get("quantity", 0),
            "unit": request_data.get("unit", "UNITS"),
            "requested_by": request_data.get("requested_by", "UNKNOWN"),
            "delivery_location": request_data.get("delivery_location", {}),
            "priority": request_data.get("priority", "MEDIUM"),
            "status": "REQUESTED",
            "eta": request_data.get("eta"),
            "justification": request_data.get("justification", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._requests[request_id] = request
        return request

    async def register_delivery(self, delivery_data: Dict[str, Any]) -> Dict[str, Any]:
        delivery_id = str(uuid.uuid4())
        request_id = delivery_data.get("request_id")
        if request_id and request_id in self._requests:
            self._requests[request_id]["status"] = "DELIVERED"

        delivery = {
            "id": delivery_id,
            "request_id": request_id,
            "supply_type": delivery_data.get("supply_type"),
            "quantity_delivered": delivery_data.get("quantity_delivered", 0),
            "delivered_by": delivery_data.get("delivered_by", "UNKNOWN"),
            "delivered_to": delivery_data.get("delivered_to", "UNKNOWN"),
            "location": delivery_data.get("location", {}),
            "status": "COMPLETED",
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "condition": delivery_data.get("condition", "GOOD"),
        }
        return delivery

    async def get_supply_status(self) -> Dict[str, Any]:
        total_supplies = len(self._supplies)
        total_requests = len(self._requests)
        pending = sum(1 for r in self._requests.values() if r["status"] == "REQUESTED")
        in_transit = sum(1 for r in self._requests.values() if r["status"] == "IN_TRANSIT")
        delivered = sum(1 for r in self._requests.values() if r["status"] == "DELIVERED")

        by_type = {}
        for s in self._supplies.values():
            st = s.get("supply_type", "OTHER")
            by_type.setdefault(st, {"available": 0, "total": 0})
            by_type[st]["total"] += 1
            if s["status"] == "AVAILABLE":
                by_type[st]["available"] += 1

        critical_shortages = []
        for s in self._supplies.values():
            if s.get("min_threshold", 0) > 0 and s.get("quantity", 0) < s["min_threshold"]:
                critical_shortages.append({
                    "supply_id": s["id"],
                    "type": s["supply_type"],
                    "current": s["quantity"],
                    "threshold": s["min_threshold"],
                })

        return {
            "total_supplies": total_supplies,
            "total_requests": total_requests,
            "pending_requests": pending,
            "in_transit": in_transit,
            "delivered": delivered,
            "by_type": by_type,
            "critical_shortages": critical_shortages,
            "chain_status": "OPERATIONAL" if not critical_shortages else "DEGRADED",
        }

    async def create_medevac(self, medevac_data: Dict[str, Any]) -> Dict[str, Any]:
        medevac_id = str(uuid.uuid4())
        medevac = {
            "id": medevac_id,
            "casualty_id": medevac_data.get("casualty_id", "UNKNOWN"),
            "casualty_name": medevac_data.get("casualty_name", ""),
            "location": medevac_data.get("location", {}),
            "urgency": medevac_data.get("urgency", "ROUTINE"),
            "type": medevac_data.get("type", "MEDEVAC"),
            "equipment_needed": medevac_data.get("equipment", []),
            "security_at_site": medevac_data.get("security", "N"),
            "marked": medevac_data.get("marked", False),
            "casualty_count": medevac_data.get("casualty_count", 1),
            "special_equipment": medevac_data.get("special_equipment", ""),
            "status": "REQUESTED",
            "classification": "SECRET",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "lines": {
                "line_1_location": medevac_data.get("location", {}),
                "line_2_radio_freq": medevac_data.get("radio_freq", ""),
                "line_3_casualties": medevac_data.get("casualty_count", 1),
                "line_4_security": medevac_data.get("security", "N"),
                "line_5_type": medevac_data.get("type", "MEDEVAC"),
                "line_6_equipment": medevac_data.get("equipment", []),
                "line_7_casualty_status": medevac_data.get("casualty_status", ""),
                "line_8_special": medevac_data.get("special_equipment", ""),
                "line_9_terrain": medevac_data.get("terrain_description", ""),
            },
        }
        self._medevacs[medevac_id] = medevac
        return medevac

    async def get_personnel_status(
        self,
        unit_id: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        personnel_list = []
        for p in self._personnel.values():
            if unit_id and p.get("unit") != unit_id:
                continue
            if status_filter and p.get("status") != status_filter:
                continue
            personnel_list.append(p)

        counts = {}
        for p in personnel_list:
            s = p.get("status", "UNKNOWN")
            counts[s] = counts.get(s, 0) + 1

        return {
            "personnel": personnel_list,
            "total": len(personnel_list),
            "status_counts": counts,
            "active_count": counts.get("ACTIVE", 0),
            "casualties": counts.get("WIA", 0) + counts.get("KIA", 0),
            "missing": counts.get("MIA", 0),
            "operational_readiness": round(
                counts.get("ACTIVE", 0) / max(len(personnel_list), 1) * 100, 1
            ),
        }

    async def add_personnel(self, personnel_data: Dict[str, Any]) -> Dict[str, Any]:
        pid = personnel_data.get("id", str(uuid.uuid4()))
        personnel = {
            "id": pid,
            "name": personnel_data.get("name", ""),
            "rank": personnel_data.get("rank", ""),
            "unit": personnel_data.get("unit", ""),
            "status": personnel_data.get("status", "ACTIVE"),
            "location": personnel_data.get("location", {}),
            "last_checkin": datetime.now(timezone.utc).isoformat(),
            "medical_status": personnel_data.get("medical_status", "FIT"),
            "role": personnel_data.get("role", ""),
        }
        self._personnel[pid] = personnel
        return personnel

    async def report_maintenance(self, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        maint_id = str(uuid.uuid4())
        report = {
            "id": maint_id,
            "equipment_id": maintenance_data.get("equipment_id", ""),
            "equipment_type": maintenance_data.get("equipment_type", ""),
            "issue_type": maintenance_data.get("issue_type", ""),
            "severity": maintenance_data.get("severity", "MEDIUM"),
            "description": maintenance_data.get("description", ""),
            "reported_by": maintenance_data.get("reported_by", ""),
            "location": maintenance_data.get("location", {}),
            "status": "REPORTED",
            "priority": maintenance_data.get("priority", "MEDIUM"),
            "estimated_repair_time_h": maintenance_data.get("estimated_repair_time_h"),
            "parts_needed": maintenance_data.get("parts_needed", []),
            "reported_at": datetime.now(timezone.utc).isoformat(),
        }
        self._maintenance[maint_id] = report
        return report


logistics_service = LogisticsService()
