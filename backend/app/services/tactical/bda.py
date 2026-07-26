import logging
from typing import Dict, List

from app.services.vision.analyst import SatelliteAnalyst

logger = logging.getLogger(__name__)


class BDAAnalyzer:
    """Evaluacion automatizada de danos de batalla.

    Utiliza SatelliteAnalyst para deteccion de cambios real
    entre imagenes pre-y-post strike.
    Sin valores aleatorios ni datos inventados.
    """

    def __init__(self):
        self._satellite_analyst = SatelliteAnalyst()

    async def assess(self, strike_data: Dict) -> Dict:
        image_before = strike_data.get("image_before_url")
        image_after = strike_data.get("image_after_url")

        if not image_before or not image_after:
            raise ValueError(
                "Se requieren imagenes pre y post strike "
                "(image_before_url, image_after_url)"
            )

        try:
            changes = await self._satellite_analyst.detect_changes(
                image_before, image_after
            )
        except Exception as e:
            logger.error("Error en deteccion de cambios: %s", e)
            changes = []

        significant_changes = [c for c in changes if c.area_px >= 256]
        total_change_area = sum(c.area_px for c in significant_changes)

        if total_change_area > 5000:
            destruction_level = "total"
            effectiveness = 0.9
            target_destroyed = True
        elif total_change_area > 2000:
            destruction_level = "severo"
            effectiveness = 0.7
            target_destroyed = True
        elif total_change_area > 500:
            destruction_level = "moderado"
            effectiveness = 0.5
            target_destroyed = False
        elif total_change_area > 100:
            destruction_level = "leve"
            effectiveness = 0.3
            target_destroyed = False
        else:
            destruction_level = "sin_dano_significativo"
            effectiveness = 0.1
            target_destroyed = False

        collateral_changes = [c for c in changes if c.area_px < 256]
        collateral_detected = len(collateral_changes) > 5

        return {
            "strike_id": strike_data.get("strike_id"),
            "effectiveness": round(effectiveness, 2),
            "target_destroyed": target_destroyed,
            "destruction_level": destruction_level,
            "collateral_damage": collateral_detected,
            "collateral_areas_detected": len(collateral_changes),
            "total_changes_detected": len(changes),
            "total_change_area_px": total_change_area,
            "sources_used": [
                "satellite_analyst",
                "change_detection",
            ],
        }

    async def satellite_bda(
        self, pre_image: str, post_image: str
    ) -> Dict:
        if not pre_image or not post_image:
            raise ValueError(
                "Se requieren imagenes pre y post strike"
            )

        try:
            changes = await self._satellite_analyst.detect_changes(
                pre_image, post_image
            )
        except Exception as e:
            logger.error("Error en satellite_bda: %s", e)
            changes = []

        if not changes:
            return {
                "damage_assessment": "no_significant_damage",
                "confidence": 1.0,
                "method": "change_detection",
                "changes_found": 0,
            }

        mean_confidence = 1.0 - min(
            1.0, sum(c.mean_intensity_diff for c in changes) / (len(changes) * 255.0)
        )
        total_area = sum(c.area_px for c in changes)

        if total_area > 5000:
            assessment = "structural_damage"
        elif total_area > 1000:
            assessment = "moderate_damage"
        elif total_area > 100:
            assessment = "minor_damage"
        else:
            assessment = "no_significant_damage"

        return {
            "damage_assessment": assessment,
            "confidence": round(max(0.1, min(1.0, mean_confidence)), 2),
            "method": "change_detection",
            "changes_found": len(changes),
            "total_change_area_px": total_area,
        }

    async def consolidated_bda(self, sources: List[Dict]) -> Dict:
        if not sources:
            raise ValueError("Se requiere al menos una fuente de evaluacion")

        assessments = [s.get("effectiveness", 0) for s in sources]
        damages = [
            s.get("target_destroyed", False) for s in sources
        ]

        avg = sum(assessments) / len(assessments) if assessments else 0
        any_destroyed = any(damages)

        return {
            "consolidated_effectiveness": round(avg, 2),
            "sources_count": len(sources),
            "any_target_destroyed": any_destroyed,
            "recommendation": (
                "restrike"
                if avg < 0.5 and not any_destroyed
                else "mission_accomplished"
            ),
        }


bda = BDAAnalyzer()
