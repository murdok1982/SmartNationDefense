# Contratos de API — SESIS-FEDERATION

`backend/contracts/` es la fuente consolidada del contrato de la API para el **namespace v1 único** (`/api/v1`).

## Archivos

| Archivo | Descripción |
| :--- | :--- |
| `openapi.json` | Especificación OpenAPI **real** generada desde la app vivo (`app.main.app.openapi()`). |
| `README.md` | Este documento. |

## Namespace V1 único

El contrato cubre el namespace único de la versión 1: todos los endpoints bajo `/api/v1`
(tabla real: `docs/architecture/CONTRACTS.md` — 134 endpoints generados de `app.main.app.openapi()`).
Routers v2/v3 (`/api/v2/*`, `/api/v3/*`) no forman parte de este contrato; si se integran al namespace v1, se regenera.

## Validación (verificación real)

```bash
cd backend
python3 -c "import json; d=json.load(open('contracts/openapi.json')); print('paths:', len(d.get('paths', {})))"
python3 -m pytest tests/test_contracts.py -q
```

## Regeneración (real)

```bash
cd backend
python3 -c "import json; from app.main import app; json.dump(app.openapi(), open('contracts/openapi.json', 'w'), indent=2)"
```

Requiere entorno con `SECRET_KEY` válido (≥ 32 caracteres; desarrollo: `SECRET_KEY="dev-s3sis-federation-secret-key-2026"`).
La tabla v1 de endpoints reales se regenera desde la app vivo con el script del rector:
`cd backend && python3 -c "... app.openapi() ..." > ../docs/architecture/CONTRACTS.md`.
