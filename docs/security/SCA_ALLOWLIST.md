# SCA Allowlist — dependencias con advisory sin parche aplicable

**Actualizado:** 21-11-2026 · **Owner:** `@redteam-auditor` / DevOps

El gate de CI ejecuta `pip-audit -r backend/requirements.txt` y
`npm audit --omit=dev --audit-level=high`. Las vulnerabilidades listadas aquí
están **explícitamente aceptadas** con justificación; cualquier otro advisory
rompe el pipeline.

## Backend (`pip-audit`)

| ID | Paquete | Motivo de la excepción | Expira |
|---|---|---|---|
| `PYSEC-2026-4298` | `python-jose 3.5.0` | Última versión publicada; no existe fix upstream. Mitigado: `algorithms=["HS256"]` fijo, sin JWE, audiencia/issuer verificados. | Revisar al publicar 3.6 |
| `PYSEC-2026-1325` | `ecdsa 0.19.2` (transitiva de `python-jose`) | Solo se usa HS256 (ECDSA no se invoca); no hay fix publicado. | Revisar con jose 3.6 |
| `PYSEC-2026-1845` | `pytest 8.3.4` | Dependencia **solo de test**, no se despliega en runtime. `pytest-asyncio 0.25` no soporta pytest 9 todavía. | Al migrar a pytest 9 |
| `PYSEC-2026-1941`, `-1942`, `-161`, `-2281`, `-2280`, `-249`, `-248` | `starlette 0.41.3` (transitiva de `fastapi 0.115.6`) | Los fixes requieren Starlette ≥1.x / FastAPI ≥0.165. Se probó la actualización: rompe la introspección de rutas del contrato y `test_contracts`/matriz de clearance. Plan de migración en `docs/ENGINEERING_RISKS.md` (FASE 10). Mitigación actual: sin uso de `StaticFiles`/formularios multipart en rutas públicas; `python-multipart` parcheado; proxies acotados. | FASE 10 |

## Frontend (`npm audit --omit=dev`)

`npm audit --omit=dev --audit-level=high` → **0 vulnerabilidades** tras el
upgrade a Next 16.4.6 / React 19.3.1 / react-leaflet 5 / lucide-react 1.77.

| Paquete | Motivo | Estado |
|---|---|---|
| `brace-expansion` (vía `eslint@9` → `minimatch`) | Dependencia **solo de desarrollo** (lint), no se incluye en el bundle de producción. `--omit=dev` la excluye del gate. Advisory de DoS local al procesar patrones glob del linter. | Aceptado en dev |
| `postcss` / `next` / `source-map-js` | Resueltos al subir de Next 14 (EOL) a Next 16.4.6; el audit de producción queda en 0. | Resuelto |

## Reglas

1. Añadir una entrada exige justificación técnica y fecha de revisión.
2. No se permite un `--ignore` sin entrada en este documento.
3. `pip-audit`/`npm audit` se ejecutan en CI **sin** `continue-on-error`.
