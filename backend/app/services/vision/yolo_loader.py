import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional

from app.core.config import settings

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

        self._verify_integrity(path)
        self._model = YOLO(str(path))
        return self._model

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _verify_integrity(self, path: Path) -> None:
        """SEC-FIX-006: pin del artefacto antes de pasarlo a torch.load.

        En production el hash es obligatorio: un `.pt` comprometido equivale
        a ejecución remota de código al deserializarse.
        """
        expected = (getattr(settings, "YOLO_MODEL_SHA256", "") or "").strip().lower()
        if expected:
            actual = self._sha256(path)
            if actual != expected:
                raise RuntimeError(
                    "YOLO model integrity check failed: sha256 no coincide con "
                    "YOLO_MODEL_SHA256"
                )
            logger.info("YOLO model sha256 verificado")
            return
        if getattr(settings, "ENVIRONMENT", "development") == "production":
            raise RuntimeError(
                "YOLO_MODEL_SHA256 es obligatorio en production: fije el hash "
                "del modelo antes de cargarlo con torch.load"
            )

    def _download(self, dest: Path) -> bool:
        if getattr(settings, "ENVIRONMENT", "development") == "production":
            logger.error(
                "Descarga automática de modelos YOLO deshabilitada en production; "
                "coloque el artefacto en %s y fije YOLO_MODEL_SHA256",
                MODEL_DIR,
            )
            return False
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
