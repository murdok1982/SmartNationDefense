# -*- coding: utf-8 -*-
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class VoiceCommandService:
    SUPPORTED_LANGUAGES = {"es", "en"}

    COMMAND_PATTERNS = {
        "es": {
            "send_message": [
                "enviar mensaje a {target}",
                "envia mensaje a {target}",
                "mensaje para {target}",
            ],
            "generate_report": [
                "generar {report_type}",
                "genera {report_type}",
                "crear {report_type}",
            ],
            "show_map": [
                "mostrar mapa de {zone}",
                "muestra mapa de {zone}",
                "ver mapa de {zone}",
            ],
            "max_alert": [
                "alerta maxima",
                "alerta max",
                "codigo rojo",
            ],
            "request_medevac": [
                "solicitar medevac",
                "solicita medevac",
                "necesito medevac",
                "evacuacion medica",
            ],
            "unit_status": [
                "estado de {unit}",
                "cual es el estado de {unit}",
                "reporte de {unit}",
            ],
            "situation_update": [
                "actualizacion de situacion",
                "situacion actual",
                "estado de la operacion",
            ],
        },
        "en": {
            "send_message": [
                "send message to {target}",
                "message to {target}",
            ],
            "generate_report": [
                "generate {report_type}",
                "create {report_type}",
            ],
            "show_map": [
                "show map of {zone}",
                "display map of {zone}",
            ],
            "max_alert": [
                "maximum alert",
                "code red",
                "red alert",
            ],
            "request_medevac": [
                "request medevac",
                "need medevac",
                "medical evacuation",
            ],
            "unit_status": [
                "status of {unit}",
                "{unit} status",
            ],
            "situation_update": [
                "situation update",
                "current situation",
                "operation status",
            ],
        },
    }

    def __init__(self):
        self._command_history: List[Dict[str, Any]] = []
        self._voice_model_status = "READY"

    async def process_command(
        self,
        audio_data: Optional[str] = None,
        text_command: Optional[str] = None,
        language: str = "es",
        user_id: str = "UNKNOWN",
    ) -> Dict[str, Any]:
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(f"Idioma no soportado: {language}")

        if text_command:
            transcript = text_command
        elif audio_data:
            transcript = await self._speech_to_text(audio_data, language)
        else:
            raise ValueError("Se requiere audio_data o text_command")

        command = self._parse_command(transcript, language)

        result = await self._execute_command(command, user_id)

        history_entry = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "language": language,
            "transcript": transcript,
            "command": command,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._command_history.append(history_entry)

        return {
            "command_id": history_entry["id"],
            "transcript": transcript,
            "language": language,
            "command_type": command.get("type", "UNKNOWN"),
            "command_params": command.get("params", {}),
            "execution_result": result,
            "confidence": command.get("confidence", 0.0),
            "timestamp": history_entry["timestamp"],
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": self._voice_model_status,
            "supported_languages": list(self.SUPPORTED_LANGUAGES),
            "total_commands_processed": len(self._command_history),
            "available_commands": list(self.COMMAND_PATTERNS["es"].keys()),
            "last_command": self._command_history[-1]["timestamp"] if self._command_history else None,
        }

    async def train_model(self, training_data: Dict[str, Any]) -> Dict[str, Any]:
        samples = training_data.get("samples", [])
        language = training_data.get("language", "es")

        return {
            "status": "COMPLETED",
            "language": language,
            "samples_processed": len(samples),
            "model_version": "1.0.1",
            "accuracy_estimate": 0.85 + min(0.1, len(samples) * 0.001),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _speech_to_text(self, audio_data: str, language: str) -> str:
        logger.info(f"Procesando audio a texto (idioma: {language})")
        return audio_data

    def _parse_command(self, transcript: str, language: str) -> Dict[str, Any]:
        transcript_lower = transcript.lower().strip()
        patterns = self.COMMAND_PATTERNS.get(language, self.COMMAND_PATTERNS["es"])

        best_match = None
        best_confidence = 0.0

        for cmd_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                confidence, params = self._match_pattern(transcript_lower, pattern)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = {
                        "type": cmd_type,
                        "params": params,
                        "confidence": confidence,
                        "matched_pattern": pattern,
                    }

        if best_match and best_confidence > 0.3:
            return best_match

        return {
            "type": "UNKNOWN",
            "params": {"raw_text": transcript},
            "confidence": 0.0,
        }

    def _match_pattern(self, text: str, pattern: str) -> tuple:
        params = {}
        pattern_parts = pattern.split()
        text_parts = text.split()

        if len(text_parts) < len(pattern_parts) - 2:
            return 0.0, {}

        matched = 0
        total = len(pattern_parts)
        param_keys = []

        for part in pattern_parts:
            if part.startswith("{") and part.endswith("}"):
                param_keys.append(part[1:-1])
                matched += 1
            elif part in text_parts:
                matched += 1

        confidence = matched / max(total, 1)

        for key in param_keys:
            idx = text_parts.index(pattern_parts[[p for p in pattern_parts if not p.startswith("{")].index(key) if key in [p for p in pattern_parts if not p.startswith("{")] else 0]) if key in text_parts else -1
            if idx >= 0 and idx < len(text_parts):
                params[key] = text_parts[idx]

        remaining_text = text.replace(pattern.split("{")[0].strip(), "").strip()
        if param_keys and remaining_text:
            for key in param_keys:
                if key not in params:
                    params[key] = remaining_text.split()[-1] if remaining_text.split() else ""

        return confidence, params

    async def _execute_command(self, command: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        cmd_type = command.get("type", "UNKNOWN")
        params = command.get("params", {})

        handlers = {
            "send_message": self._handle_send_message,
            "generate_report": self._handle_generate_report,
            "show_map": self._handle_show_map,
            "max_alert": self._handle_max_alert,
            "request_medevac": self._handle_request_medevac,
            "unit_status": self._handle_unit_status,
            "situation_update": self._handle_situation_update,
        }

        handler = handlers.get(cmd_type, self._handle_unknown)
        return await handler(params, user_id)

    async def _handle_send_message(self, params: Dict, user_id: str) -> Dict[str, Any]:
        target = params.get("target", "UNKNOWN")
        return {
            "status": "QUEUED",
            "message": f"Mensaje preparado para {target}",
            "action": "send_message",
            "target": target,
            "requires_confirmation": True,
        }

    async def _handle_generate_report(self, params: Dict, user_id: str) -> Dict[str, Any]:
        report_type = params.get("report_type", "SITREP").upper()
        return {
            "status": "GENERATING",
            "message": f"Generando reporte {report_type}",
            "action": "generate_report",
            "report_type": report_type,
        }

    async def _handle_show_map(self, params: Dict, user_id: str) -> Dict[str, Any]:
        zone = params.get("zone", "AREA_OPERACIONES")
        return {
            "status": "DISPLAYED",
            "message": f"Mostrando mapa de {zone}",
            "action": "show_map",
            "zone": zone,
        }

    async def _handle_max_alert(self, params: Dict, user_id: str) -> Dict[str, Any]:
        return {
            "status": "ACTIVATED",
            "message": "Alerta maxima activada",
            "action": "max_alert",
            "alert_level": "MAXIMUM",
        }

    async def _handle_request_medevac(self, params: Dict, user_id: str) -> Dict[str, Any]:
        return {
            "status": "QUEUED",
            "message": "Solicitud MEDEVAC iniciada",
            "action": "request_medevac",
            "requires_confirmation": True,
        }

    async def _handle_unit_status(self, params: Dict, user_id: str) -> Dict[str, Any]:
        unit = params.get("unit", "UNKNOWN")
        return {
            "status": "RETRIEVING",
            "message": f"Consultando estado de {unit}",
            "action": "unit_status",
            "unit": unit,
        }

    async def _handle_situation_update(self, params: Dict, user_id: str) -> Dict[str, Any]:
        return {
            "status": "GENERATING",
            "message": "Generando actualizacion de situacion",
            "action": "situation_update",
        }

    async def _handle_unknown(self, params: Dict, user_id: str) -> Dict[str, Any]:
        return {
            "status": "NOT_RECOGNIZED",
            "message": "Comando no reconocido",
            "action": "unknown",
            "raw_text": params.get("raw_text", ""),
        }


voice_command_service = VoiceCommandService()
