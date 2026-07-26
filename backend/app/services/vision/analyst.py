import os
import uuid
import logging
import tempfile
from typing import List, Optional
from pathlib import Path

from pydantic import BaseModel, Field

from app.services.vision.yolo_loader import YOLOLoader

logger = logging.getLogger(__name__)


class Detection(BaseModel):
    bbox: List[float] = Field(..., description="[x1, y1, x2, y2] en píxeles")
    confidence: float = Field(ge=0.0, le=1.0)
    class_id: int
    class_name: str


class Change(BaseModel):
    bbox: List[float]
    area_px: int
    mean_intensity_diff: float
    label: str = "change"


class TargetClassification(BaseModel):
    target_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    category: str
    attributes: dict = Field(default_factory=dict)
    recommendation: str = ""


class SatelliteAnalyst:
    def __init__(
        self,
        temp_dir: Optional[str] = None,
        min_area: int = 64,
        yolo_model_path: str = "yolov8n.pt",
    ):
        self.temp_dir = Path(temp_dir or tempfile.gettempdir()) / "sesis-vision"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.min_area = min_area
        self.yolo_model_path = yolo_model_path
        self._yolo_model = None

    async def _download_image(self, url: str) -> str:
        import httpx
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            ext = ".jpg"
            fname = f"{uuid.uuid4().hex}{ext}"
            path = str(self.temp_dir / fname)
            with open(path, "wb") as f:
                f.write(resp.content)
            return path

    def _cleanup(self, path: str):
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception as e:
            logger.warning("cleanup error %s: %s", path, e)

    async def detect_objects(
        self, image_url: str, model_type: str = "yolo"
    ) -> List[Detection]:
        path = None
        try:
            path = await self._download_image(image_url)
            return await self._detect_yolo(path)
        except Exception as e:
            logger.error("detect_objects error: %s", e)
            raise
        finally:
            if path:
                self._cleanup(path)

    async def _detect_yolo(self, path: str) -> List[Detection]:
        if self._yolo_model is None:
            loader = YOLOLoader()
            self._yolo_model = loader.load(self.yolo_model_path)
        results = self._yolo_model(path)
        dets: List[Detection] = []
        for r in results:
            if r.boxes is None:
                continue
            for box, conf, cls_id in zip(r.boxes.xyxy, r.boxes.conf, r.boxes.cls):
                dets.append(
                    Detection(
                        bbox=[float(box[0]), float(box[1]), float(box[2]), float(box[3])],
                        confidence=float(conf),
                        class_id=int(cls_id),
                        class_name=r.names[int(cls_id)],
                    )
                )
        return dets

    async def detect_changes(
        self, before_url: str, after_url: str, min_area: int = 64
    ) -> List[Change]:
        try:
            import cv2
            import numpy as np
        except ImportError:
            raise RuntimeError(
                "OpenCV y numpy son necesarios para detect_changes. "
                "instálalos con: pip install opencv-python-headless numpy"
            )
        before_path = None
        after_path = None
        try:
            before_path = await self._download_image(before_url)
            after_path = await self._download_image(after_url)
            img_before = cv2.imread(before_path, cv2.IMREAD_GRAYSCALE)
            img_after = cv2.imread(after_path, cv2.IMREAD_GRAYSCALE)
            if img_before is None or img_after is None:
                raise RuntimeError("No se pudieron leer las imágenes para change detection")
            if img_before.shape != img_after.shape:
                img_after = cv2.resize(img_after, (img_before.shape[1], img_before.shape[0]))
            diff = cv2.absdiff(img_before, img_after)
            _, mask = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            changes: List[Change] = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < min_area:
                    continue
                x, y, w, h = cv2.boundingRect(cnt)
                region = diff[y : y + h, x : x + w]
                mean_diff = float(np.mean(region))
                changes.append(
                    Change(
                        bbox=[float(x), float(y), float(x + w), float(y + h)],
                        area_px=int(area),
                        mean_intensity_diff=round(mean_diff, 2),
                    )
                )
            return changes
        finally:
            if before_path:
                self._cleanup(before_path)
            if after_path:
                self._cleanup(after_path)

    def classify_target(
        self, detection: Detection, context: Optional[dict] = None
    ) -> TargetClassification:
        w = detection.bbox[2] - detection.bbox[0]
        h = detection.bbox[3] - detection.bbox[1]
        aspect = w / max(h, 1)
        area = w * h

        if detection.class_name in ("car", "truck", "bus", "vehicle"):
            if aspect > 1.8:
                return TargetClassification(
                    target_type="vehiculo_militar_ligero",
                    confidence=0.65,
                    category="vehiculo",
                    attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area)},
                    recommendation="verificar identificacion amigo/enemigo",
                )
            return TargetClassification(
                target_type="vehiculo_civil",
                confidence=0.55,
                category="vehiculo",
                attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area)},
                recommendation="monitorear desplazamiento",
            )

        if detection.class_name in ("person",):
            if h > w * 2.5:
                return TargetClassification(
                    target_type="infanteria",
                    confidence=0.7,
                    category="personal",
                    attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area)},
                    recommendation="posible combatiente - confirmar con otra fuente",
                )
            return TargetClassification(
                target_type="civil",
                confidence=0.5,
                category="personal",
                attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area)},
                recommendation="probable no combatiente",
            )

        if detection.class_name in ("airplane", "helicopter", "drone", "uav"):
            return TargetClassification(
                target_type="aeronave",
                confidence=0.75,
                category="aereo",
                attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area)},
                recommendation="rastrear trayectoria y origen",
            )

        if detection.class_name in ("fortification", "bunker"):
            return TargetClassification(
                target_type="fortificacion",
                confidence=0.8,
                category="infraestructura",
                attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area)},
                recommendation="incluir en plan de fuegos",
            )

        return TargetClassification(
            target_type="no_clasificado",
            confidence=0.3,
            category="desconocido",
            attributes={"aspect_ratio": round(aspect, 2), "area_px": int(area), "class": detection.class_name},
            recommendation="requiere analisis adicional",
        )
