import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    pass

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "yolov8n.pt"


class YOLOLoader:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, model_path: Optional[str] = None):
        if self._model is not None:
            return self._model

        if not _YOLO_AVAILABLE:
            raise RuntimeError(
                "ultralytics no está instalado. "
                "Ejecuta: pip install ultralytics"
            )

        path = Path(model_path) if model_path else MODEL_PATH

        if not path.exists():
            if not self._download(path):
                raise RuntimeError(
                    f"YOLO model not found at {path}. "
                    "Run with internet first or place model at: "
                    f"{MODEL_DIR}"
                )

        self._model = YOLO(str(path))
        return self._model

    def _download(self, dest: Path) -> bool:
        try:
            logger.info("Descargando YOLOv8n desde ultralytics...")
            model = YOLO("yolov8n.pt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            src = Path.home() / ".cache" / "ultralytics" / "models" / "yolov8n.pt"
            if src.exists():
                shutil.copy2(str(src), str(dest))
                logger.info("Modelo guardado en %s", dest)
                return True
            local = Path("yolov8n.pt")
            if local.exists():
                shutil.copy2(str(local), str(dest))
                return True
            logger.warning("No se encontró el modelo descargado en cache")
            return False
        except Exception as e:
            logger.warning("No se pudo descargar YOLO: %s", e)
            return False

    @property
    def is_available(self) -> bool:
        return _YOLO_AVAILABLE

    def unload(self):
        self._model = None
        YOLOLoader._instance = None
