# -*- coding: utf-8 -*-
import uuid
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class ReportsService:
    def __init__(self):
        self._reports: Dict[str, Dict[str, Any]] = {}

    async def generate_sitrep(self, sitrep_data: Dict[str, Any]) -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        content = {
            "header": {
                "classification": sitrep_data.get("classification", "CONFIDENTIAL"),
                "report_type": "SITREP",
                "report_id": report_id,
                "dtg": now,
                "from": sitrep_data.get("from_unit", ""),
                "to": sitrep_data.get("to_unit", ""),
                "ref": sitrep_data.get("reference", ""),
            },
            "section_1_situation": {
                "enemy_forces": sitrep_data.get("enemy_forces", ""),
                "friendly_forces": sitrep_data.get("friendly_forces", ""),
                "attachments_detachments": sitrep_data.get("attachments", ""),
            },
            "section_2_weather": {
                "current": sitrep_data.get("weather_current", ""),
                "forecast_12h": sitrep_data.get("weather_forecast_12h", ""),
                "forecast_24h": sitrep_data.get("weather_forecast_24h", ""),
            },
            "section_3_operations": {
                "ongoing": sitrep_data.get("operations_ongoing", []),
                "completed": sitrep_data.get("operations_completed", []),
                "planned": sitrep_data.get("operations_planned", []),
            },
            "section_4_logistics": {
                "supply_status": sitrep_data.get("supply_status", ""),
                "critical_needs": sitrep_data.get("critical_needs", []),
            },
            "section_5_personnel": {
                "strength": sitrep_data.get("personnel_strength", ""),
                "casualties": sitrep_data.get("casualties", ""),
                "morale": sitrep_data.get("morale", ""),
            },
            "section_6_signal": {
                "comms_status": sitrep_data.get("comms_status", ""),
                "frequency_changes": sitrep_data.get("frequency_changes", ""),
            },
        }

        report = self._create_report(
            report_id=report_id,
            report_type="SITREP",
            title=f"SITREP - {sitrep_data.get('from_unit', 'UNKNOWN')} - {now[:10]}",
            content=content,
            classification=sitrep_data.get("classification", "CONFIDENTIAL"),
            created_by=sitrep_data.get("created_by", "SYSTEM"),
            distribution_list=sitrep_data.get("distribution_list", []),
            operation_id=sitrep_data.get("operation_id"),
        )
        return report

    async def generate_spotrep(self, spotrep_data: Dict[str, Any]) -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        content = {
            "header": {
                "classification": spotrep_data.get("classification", "CONFIDENTIAL"),
                "report_type": "SPOTREP",
                "report_id": report_id,
                "dtg": now,
            },
            "size": spotrep_data.get("size", ""),
            "activity": spotrep_data.get("activity", ""),
            "location": spotrep_data.get("location", {}),
            "unit": spotrep_data.get("unit_identified", ""),
            "time": spotrep_data.get("time_observed", now),
            "equipment": spotrep_data.get("equipment", ""),
            "narrative": spotrep_data.get("narrative", ""),
            "assessment": spotrep_data.get("assessment", ""),
        }

        report = self._create_report(
            report_id=report_id,
            report_type="SPOTREP",
            title=f"SPOTREP - {spotrep_data.get('location', {}).get('grid', 'UNKNOWN')} - {now[:10]}",
            content=content,
            classification=spotrep_data.get("classification", "CONFIDENTIAL"),
            created_by=spotrep_data.get("created_by", "SYSTEM"),
            distribution_list=spotrep_data.get("distribution_list", []),
        )
        return report

    async def generate_salute(self, salute_data: Dict[str, Any]) -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        content = {
            "header": {
                "classification": salute_data.get("classification", "CONFIDENTIAL"),
                "report_type": "SALUTE",
                "report_id": report_id,
                "dtg": now,
            },
            "S_size": salute_data.get("size", ""),
            "A_activity": salute_data.get("activity", ""),
            "L_location": salute_data.get("location", {}),
            "U_unit": salute_data.get("unit", ""),
            "T_time": salute_data.get("time", now),
            "E_equipment": salute_data.get("equipment", ""),
            "assessment": salute_data.get("assessment", ""),
            "source_reliability": salute_data.get("source_reliability", "B"),
            "info_credibility": salute_data.get("info_credibility", "2"),
        }

        report = self._create_report(
            report_id=report_id,
            report_type="SALUTE",
            title=f"SALUTE Report - {now[:10]}",
            content=content,
            classification=salute_data.get("classification", "CONFIDENTIAL"),
            created_by=salute_data.get("created_by", "SYSTEM"),
            distribution_list=salute_data.get("distribution_list", []),
        )
        return report

    async def generate_medevac_report(self, mevdecac_data: Dict[str, Any]) -> Dict[str, Any]:
        report_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        content = {
            "header": {
                "classification": "SECRET",
                "report_type": "MEDEVAC",
                "report_id": report_id,
                "dtg": now,
                "priority": mevdecac_data.get("urgency", "ROUTINE"),
            },
            "line_1_pickup_location": mevdecac_data.get("pickup_location", {}),
            "line_2_radio_freq": mevdecac_data.get("radio_freq", ""),
            "line_3_casualties": {
                "total": mevdecac_data.get("casualty_count", 0),
                "urgent": mevdecac_data.get("urgent_count", 0),
                "priority": mevdecac_data.get("priority_count", 0),
                "routine": mevdecac_data.get("routine_count", 0),
            },
            "line_4_security": mevdecac_data.get("security", "N"),
            "line_5_type": mevdecac_data.get("evac_type", "MEDEVAC"),
            "line_6_equipment": mevdecac_data.get("equipment", []),
            "line_7_casualty_status": mevdecac_data.get("casualty_status", ""),
            "line_8_special_equipment": mevdecac_data.get("special_equipment", ""),
            "line_9_terrain": mevdecac_data.get("terrain", ""),
            "requesting_unit": mevdecac_data.get("requesting_unit", ""),
            "commander_name": mevdecac_data.get("commander_name", ""),
        }

        report = self._create_report(
            report_id=report_id,
            report_type="MEDEVAC",
            title=f"MEDEVAC Request - {mevdecac_data.get('urgency', 'ROUTINE')}",
            content=content,
            classification="SECRET",
            created_by=mevdecac_data.get("created_by", "SYSTEM"),
            distribution_list=mevdecac_data.get("distribution_list", []),
        )
        return report

    async def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        return self._reports.get(report_id)

    async def list_reports(
        self,
        report_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        results = []
        for r in self._reports.values():
            if report_type and r.get("report_type") != report_type:
                continue
            results.append(r)
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[offset:offset + limit]

    def _create_report(
        self,
        report_id: str,
        report_type: str,
        title: str,
        content: Dict[str, Any],
        classification: str,
        created_by: str,
        distribution_list: List[str],
        operation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        signature = self._generate_signature(content, created_by)
        report = {
            "id": report_id,
            "report_type": report_type,
            "title": title,
            "content": content,
            "classification": classification,
            "distribution_list": distribution_list,
            "digital_signature": signature,
            "auto_generated": True,
            "source_data": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": created_by,
            "operation_id": operation_id,
            "status": "FINAL",
        }
        self._reports[report_id] = report
        return report

    def _generate_signature(self, content: Dict[str, Any], author: str) -> str:
        import json
        data = json.dumps(content, sort_keys=True).encode()
        return hashlib.sha256(data + author.encode()).hexdigest()


reports_service = ReportsService()
