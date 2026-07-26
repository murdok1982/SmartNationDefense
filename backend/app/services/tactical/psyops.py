import logging
from typing import Dict, Any, Optional

from app.core.classification import ClassificationLevel
from app.services.intel.llm.router import llm_router
from app.services.intel.llm.base import LLMTask

logger = logging.getLogger(__name__)


MESSAGE_TEMPLATES = {
    "leaflet": {
        "format": "panfleto_impreso",
        "sections": ["encabezado", "mensaje_principal", "llamado_accion", "pie_informativo"],
        "max_length_chars": 500,
    },
    "loudspeaker": {
        "format": "difusion_altavoz",
        "sections": ["saludo", "instruccion", "advertencia", "cierre"],
        "max_length_chars": 300,
    },
    "radio": {
        "format": "transmision_radio",
        "sections": ["identificacion_emisora", "mensaje", "frecuencia_siguiente"],
        "max_length_chars": 200,
    },
    "social_media": {
        "format": "publicacion_red_social",
        "sections": ["contenido_visual", "texto_principal", "hashtags"],
        "max_length_chars": 1000,
    },
}


CAMPAIGN_STRUCTURE = {
    "required_fields": [
        "target_audience",
        "objective",
        "themes",
        "channels",
        "duration_days",
    ],
    "phases": [
        {
            "name": "intelligence_preparation",
            "activities": [
                "analisis_audiencia",
                "identificacion_mensajes_clave",
                "evaluacion_vulnerabilidades",
            ],
        },
        {
            "name": "message_development",
            "activities": [
                "creacion_contenido",
                "traduccion_adaptacion",
                "aprobacion_mando",
            ],
        },
        {
            "name": "dissemination",
            "activities": [
                "difusion_canales_asignados",
                "monitoreo_tiempo_real",
            ],
        },
        {
            "name": "effectiveness_assessment",
            "activities": [
                "encuestas_opinion",
                "analisis_cambio_comportamiento",
                "informe_final",
            ],
        },
    ],
}


class PSYOPSGenerator:
    """Generador de mensajes y campanas de Operaciones Psicologicas.

    La estructura de mensajes sigue formatos tacticos estandar
    (panfletos, altavoz, radio, redes sociales).
    El contenido es generado por el LLM con prompts especificos
    para cada tipo de audiencia y objetivo.
    """

    async def generate_message(
        self,
        target_audience: str,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
        channel: str = "leaflet",
    ) -> str:
        template = MESSAGE_TEMPLATES.get(channel, MESSAGE_TEMPLATES["leaflet"])
        context_str = f"Contexto: {context}" if context else ""

        prompt = (
            f"Genera un mensaje de operaciones psicologicas para "
            f"audiencia '{target_audience}' con objetivo '{objective}'. "
            f"Formato: {template['format']}. "
            f"Secciones requeridas: {', '.join(template['sections'])}. "
            f"Maximo {template['max_length_chars']} caracteres. "
            f"{context_str}\n\n"
            f"El mensaje debe ser culturalmente apropiado, "
            f"psicologicamente efectivo y conforme a ROE."
        )

        try:
            result = await llm_router.generate(
                LLMTask(
                    prompt=prompt,
                    system_prompt=(
                        "Eres un especialista en operaciones psicologicas. "
                        "Genera mensajes persuasivos pero factuales, "
                        "sin incitar a la violencia ni violar derechos humanos."
                    ),
                    classification=ClassificationLevel.CONFIDENTIAL,
                    temperature=0.4,
                )
            )
            return result.text
        except Exception as e:
            logger.warning("LLM no disponible para PSYOPS: %s", e)
            return await self._fallback_generate(target_audience, objective, channel)

    async def _fallback_generate(
        self, target_audience: str, objective: str, channel: str
    ) -> str:
        template = MESSAGE_TEMPLATES.get(channel, MESSAGE_TEMPLATES["leaflet"])
        return (
            f"[{template['format'].upper()}] "
            f"AUDIENCIA: {target_audience} | "
            f"OBJETIVO: {objective} | "
            f"CONTENIDO: [Requiere LLM disponible]" 
        )

    async def plan_campaign(
        self, campaign_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        missing = [
            f
            for f in CAMPAIGN_STRUCTURE["required_fields"]
            if f not in campaign_params
        ]
        if missing:
            raise ValueError(
                f"Parametros requeridos faltantes: {', '.join(missing)}"
            )

        phases = []
        for i, phase_tpl in enumerate(CAMPAIGN_STRUCTURE["phases"]):
            phases.append(
                {
                    "phase": i + 1,
                    "name": phase_tpl["name"],
                    "activities": phase_tpl["activities"],
                    "duration_days": campaign_params.get("duration_days", 10)
                    // len(CAMPAIGN_STRUCTURE["phases"]),
                }
            )

        messages = []
        channels = campaign_params.get("channels", ["leaflet"])
        for channel in channels:
            msg = await self.generate_message(
                target_audience=campaign_params["target_audience"],
                objective=campaign_params["objective"],
                context=campaign_params.get("context"),
                channel=channel,
            )
            messages.append({"channel": channel, "content": msg})

        return {
            "name": campaign_params.get("name", "campana_sin_nombre"),
            "phases": phases,
            "messages": messages,
            "channels": channels,
            "themes": campaign_params.get("themes", []),
        }

    async def generate_deception_plan(
        self, operation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        prompt = (
            f"Genera un plan de ninezi/decepcion tactica de tipo "
            f"'{operation_params.get('type', 'camouflage')}' "
            f"para '{operation_params.get('operation_name', 'operacion')}'. "
            f"Story de cobertura: '{operation_params.get('cover_story', '')}'. "
            f"Incluye: medidas de ninezi, senuelos, ninezi electronica."
        )

        try:
            result = await llm_router.generate(
                LLMTask(
                    prompt=prompt,
                    system_prompt=(
                        "Eres un especialista en ninezi y decepcion militar. "
                        "Genera planes realistas basados en doctrina."
                    ),
                    classification=ClassificationLevel.SECRET,
                    temperature=0.3,
                )
            )
            content = result.text
        except Exception as e:
            logger.warning("LLM no disponible para deception plan: %s", e)
            content = "[Requiere LLM disponible]"

        return {
            "deception_type": operation_params.get("type", "camouflage"),
            "measures": [
                "senuelos_inflables",
                "trafico_radio_falso",
                "posiciones_decoys",
                "ninezi_electronica",
            ],
            "cover_story": operation_params.get("cover_story", ""),
            "llm_generated_content": content,
        }


psyops = PSYOPSGenerator()
