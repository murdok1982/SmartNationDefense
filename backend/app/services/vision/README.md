# Pipeline de Visión por Computadora — SESIS FEDERATION

## Dependencias

```bash
pip install ultralytics torch opencv-python-headless numpy
```

Todo está declarado en `requirements.txt`.

## Modelo YOLO para demo offline

El pipeline usa **YOLOv8n** (Nano, ~6 MB) para detección de objetos en imágenes satelitales y drones. No hay fallback; si YOLO no está disponible, la API responde con **501 Service Unavailable**.

### Primera vez (con internet)

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

Esto descarga el modelo a `~/.cache/ultralytics/models/yolov8n.pt`.

Luego, cópialo al directorio local del proyecto:

```bash
python -c "
from pathlib import Path
import shutil
src = Path.home() / '.cache' / 'ultralytics' / 'models' / 'yolov8n.pt'
dst = Path('app/services/vision/models/yolov8n.pt')
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(str(src), str(dst))
print('Modelo copiado a', dst)
"
```

O simplemente arranca el backend con internet y el `YOLOLoader` lo descargará automáticamente al primer `detect_objects`.

### Sin internet (demo offline)

1. En una máquina con internet, ejecuta el paso anterior.
2. Copia la carpeta `backend/app/services/vision/models/` completa a la máquina offline.
3. Verifica que el archivo `models/yolov8n.pt` exista.

### Verificación

```bash
cd backend
python -c "
from app.services.vision.yolo_loader import YOLOLoader
model = YOLOLoader().load()
print('YOLO cargado correctamente:', model)
"
```

## Estructura

```
vision/
├── __init__.py           # Exporta SatelliteAnalyst, DroneFeedProcessor, YOLOLoader
├── analyst.py            # SatelliteAnalyst: detección y clasificación con YOLO
├── drone_processor.py    # DroneFeedProcessor: análisis de video en tiempo real
├── yolo_loader.py        # YOLOLoader singleton: carga/descarga del modelo
├── models/
│   ├── .gitkeep          # Directorio para el modelo .pt
│   └── yolov8n.pt        # Modelo YOLOv8n (no trackeado en git)
└── README.md
```

## Notas

- `ultralytics` es una dependencia **obligatoria** en producción. Sin ella, `detect_objects` lanza `RuntimeError` y la API devuelve 501.
- `DroneFeedProcessor` usa solo OpenCV (sin YOLO) para detección basada en movimiento.
- `detect_changes` usa差值 de frames con OpenCV; requiere `opencv-python-headless` y `numpy`.
