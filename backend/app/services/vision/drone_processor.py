import logging
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_CV2_AVAILABLE = False
_NP_AVAILABLE = False

try:
    import numpy as np
    _NP_AVAILABLE = True
except ImportError:
    pass

try:
    import cv2
    _CV2_AVAILABLE = True
except ImportError:
    pass


class Detection(BaseModel):
    bbox: List[float]
    confidence: float = Field(ge=0.0, le=1.0)
    class_id: int
    class_name: str


class FrameAnalysis(BaseModel):
    timestamp: str
    source: str
    detections: List[Detection] = Field(default_factory=list)
    activity_heatmap: Optional[str] = None
    frame_width: int = 0
    frame_height: int = 0


class DroneFeedProcessor:
    def __init__(
        self,
        nms_threshold: float = 0.5,
        temporal_window: float = 0.5,
        min_confidence: float = 0.35,
    ):
        if not _CV2_AVAILABLE or not _NP_AVAILABLE:
            raise RuntimeError(
                "OpenCV y numpy son obligatorios para DroneFeedProcessor. "
                "Instala: pip install opencv-python-headless numpy"
            )
        self.nms_threshold = nms_threshold
        self.temporal_window = temporal_window
        self.min_confidence = min_confidence
        self._track_buffer: deque = deque(maxlen=30)

    def analyze_frame(self, frame: "np.ndarray", source: str = "drone") -> FrameAnalysis:
        import numpy as np
        import cv2
        h, w = frame.shape[:2]
        detections = self._detect_frame(frame)
        detections = self._temporal_nms(detections)
        heatmap = self._compute_heatmap(frame)
        _, buffer = cv2.imencode(".jpg", heatmap)
        import base64
        heatmap_b64 = base64.b64encode(buffer.tobytes()).decode("utf-8")
        self._track_buffer.append({
            "ts": time.time(),
            "detections": detections,
        })
        return FrameAnalysis(
            timestamp=datetime.now(timezone.utc).isoformat(),
            source=source,
            detections=detections,
            activity_heatmap=heatmap_b64,
            frame_width=w,
            frame_height=h,
        )

    def _detect_frame(self, frame: "np.ndarray") -> List[Detection]:
        import cv2
        import numpy as np
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        dets: List[Detection] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 64:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            conf = min(1.0, area / 5000.0)
            if conf < self.min_confidence:
                continue
            dets.append(
                Detection(
                    bbox=[float(x), float(y), float(x + w), float(y + h)],
                    confidence=conf,
                    class_id=0,
                    class_name="object",
                )
            )
        return dets

    def _temporal_nms(self, detections: List[Detection]) -> List[Detection]:
        if not detections:
            return []
        if not self._track_buffer:
            return detections
        recent = [d for d in detections]
        for entry in list(self._track_buffer):
            if time.time() - entry["ts"] > self.temporal_window:
                continue
            for prev in entry["detections"]:
                for curr in detections:
                    if self._iou(prev.bbox, curr.bbox) > self.nms_threshold:
                        if curr in recent:
                            recent.remove(curr)
        return recent

    def _compute_heatmap(self, frame: "np.ndarray") -> "np.ndarray":
        import cv2
        import numpy as np
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fgbg = cv2.createBackgroundSubtractorMOG2()
        fgmask = fgbg.apply(gray)
        heat = cv2.applyColorMap(fgmask, cv2.COLORMAP_JET)
        return cv2.addWeighted(frame, 0.6, heat, 0.4, 0)

    @staticmethod
    def _iou(bbox_a: List[float], bbox_b: List[float]) -> float:
        xA = max(bbox_a[0], bbox_b[0])
        yA = max(bbox_a[1], bbox_b[1])
        xB = min(bbox_a[2], bbox_b[2])
        yB = min(bbox_a[3], bbox_b[3])
        inter = max(0, xB - xA) * max(0, yB - yA)
        area_a = (bbox_a[2] - bbox_a[0]) * (bbox_a[3] - bbox_a[1])
        area_b = (bbox_b[2] - bbox_b[0]) * (bbox_b[3] - bbox_b[1])
        union = area_a + area_b - inter
        return inter / max(union, 1e-6)
