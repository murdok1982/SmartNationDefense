import base64
import io
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v3.deps import get_current_user_v3
from app.services.vision.analyst import SatelliteAnalyst
from app.services.vision.drone_processor import DroneFeedProcessor
from app.services.fusion.engine import FusionEngine, SensorEvent
from app.services.fusion.jdl_fusion import jdl_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Maven"])

_satellite_analyst = SatelliteAnalyst()
_fusion_engine = FusionEngine()
_drone_processor: Optional[DroneFeedProcessor] = None

def _get_drone_processor() -> Optional[DroneFeedProcessor]:
    global _drone_processor
    if _drone_processor is not None:
        return _drone_processor
    try:
        _drone_processor = DroneFeedProcessor()
    except RuntimeError as e:
        logger.warning("DroneFeedProcessor no disponible: %s", e)
    return _drone_processor


@router.post("/vision/analyze-satellite")
async def analyze_satellite(
    image_url: str,
    model_type: str = "yolo",
    user: dict = Depends(get_current_user_v3),
):
    try:
        detections = await _satellite_analyst.detect_objects(image_url, model_type)
        classifications = []
        for det in detections:
            tc = _satellite_analyst.classify_target(det)
            classifications.append(tc.model_dump())
        return {
            "detections": [d.model_dump() for d in detections],
            "classifications": classifications,
            "count": len(detections),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"URL rechazada: {e}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error descargando imagen: {e}")
    except Exception:
        logger.exception("analyze-satellite error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno en analisis de imagen")


@router.post("/vision/detect-changes")
async def detect_changes(
    before_url: str,
    after_url: str,
    min_area: int = 64,
    user: dict = Depends(get_current_user_v3),
):
    try:
        changes = await _satellite_analyst.detect_changes(before_url, after_url, min_area)
        return {"changes": [c.model_dump() for c in changes], "count": len(changes)}
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"URL rechazada: {e}")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Error descargando imágenes: {e}")
    except Exception:
        logger.exception("detect-changes error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno en deteccion de cambios")


@router.post("/vision/drone-frame")
async def drone_frame(
    frame_url: Optional[str] = None,
    frame_base64: Optional[str] = None,
    source: str = "drone",
    user: dict = Depends(get_current_user_v3),
):
    dp = _get_drone_processor()
    if dp is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="DroneFeedProcessor no disponible: OpenCV/numpy no instalados",
        )
    if not frame_url and not frame_base64:
        raise HTTPException(status_code=400, detail="Se requiere frame_url o frame_base64")
    import numpy as np
    import cv2
    frame: Optional[np.ndarray] = None
    if frame_url:
        from app.services.osint.tools.web_tools import safe_http_get
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=False) as client:
                resp = await safe_http_get(client, frame_url, max_redirects=3)
                resp.raise_for_status()
                data = resp.content
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"URL bloqueada: {e}")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Error descargando frame: {e}")
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    elif frame_base64:
        try:
            data = base64.b64decode(frame_base64)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Base64 inválido: {e}")
        arr = np.frombuffer(data, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="No se pudo decodificar el frame")
    analysis = dp.analyze_frame(frame, source=source)
    return analysis.model_dump()


@router.get("/fusion/cop")
async def get_cop(user: dict = Depends(get_current_user_v3)):
    return _fusion_engine.get_cop_snapshot().model_dump()


@router.post("/fusion/ingest-event")
async def ingest_event(
    event: SensorEvent,
    user: dict = Depends(get_current_user_v3),
):
    track = await _fusion_engine.ingest(event)
    return {
        "status": "ingested",
        "track_id": track.track_id,
        "total_events_in_track": len(track.events),
    }


@router.get("/fusion/jdl-pipeline")
async def jdl_pipeline_endpoint(
    user: dict = Depends(get_current_user_v3),
):
    result = await jdl_pipeline.run_full_pipeline(
        raw_signals=[],
        raw_detections=[],
    )
    return result.model_dump()
