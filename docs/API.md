# API.md — Contrato HTTP real (SESIS-FEDERATION)

**Doc ID:** API-2026-SND-001
**Fuente de verdad:** `backend/contracts/openapi.json` generado desde `app.main.app`
**Paths:** 168 · **Operaciones:** 177
**Fecha:** 2026-11-21
**Verificación:** introspección de la app viva + parseo del contrato
**Validación cruzada:** 157 tests backend, 88% de cobertura en las 6 suites de seguridad (backend completo ≈73%, no al 80%), móvil 0 errores/11 tests, frontend Next 16 verificado; el contrato no cambió (168 paths / 177 operaciones).

> **Regla:** este documento no inventa endpoints. Cada fila existe en el OpenAPI generado. Cuando un endpoint existe pero su implementación es un stub, se indica en la columna «Implementación». Para el detalle de comportamiento ver `docs/FEATURE_MATRIX.md`.

---

## 1. Resumen del contrato

### 1.1 Conteo por prefijo

| Prefijo | Paths | Operaciones | Naturaleza |
| :--- | ---: | ---: | :--- |
| `/` | 1 | 1 | Servicio |
| `/api/v1` | 129 | 134 | Dominio legacy + táctico |
| `/api/v2` | 27 | 31 | Dominios avanzados |
| `/api/v3` | 11 | 11 | Maven / COA |
| **Total** | **168** | **177** | |

### 1.2 Comando de regeneración

```bash
cd backend
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -c \
  "import json; from app.main import app; json.dump(app.openapi(), open('contracts/openapi.json','w'), indent=2)"
```

El test `backend/tests/test_contracts.py` comprueba que el contrato no se aleje de la app viva (5 tests).

### 1.3 Advertencia de lectura

El contrato describe **rutas existentes**, no **capacidades completas**. En particular:

- `/api/v1/osint/*` (6 paths): stub de listas vacías.
- `/api/v1/intel/*` (3 paths): stub de listas vacías.
- `/api/v1/satellite/*` (2 paths): estado fijo y `queued`.
- `/api/v1/agents/*` (15 paths): estado fijo y respuestas mínimas.
- `/api/v1/media/*` **no aparece**: el router existe pero no está montado.

Un cliente que se guíe sólo por OpenAPI puede asumir que esas capacidades están operativas. No lo están. Ver §5.

---

## 2. Convenciones

### 2.1 Base y versionado

| Elemento | Valor |
| :--- | :--- |
| Base local | `http://localhost:8000` |
| Base tras Nginx | `https://localhost` |
| Versiones | `/api/v1`, `/api/v2`, `/api/v3` |
| Formato | JSON UTF-8 |
| Documentación interactiva | `/docs` (dev) |
| Esquema | `/openapi.json` y `backend/contracts/openapi.json` |

### 2.2 Autenticación

```http
Authorization: Bearer <access_token>
```

| Token | TTL | Uso |
| :--- | :--- | :--- |
| Access | 15 min | Rutas protegidas |
| Refresh | 7 días | Renovación con rotación |
| MFA challenge | 5 min | Sólo verificación MFA; rechazado como bearer |

Reglas verificadas:

- Un refresh token no puede usarse como access (`decode_token(..., is_refresh=True)`).
- Un ticket MFA no puede usarse como access (`expected_type`).
- El logout revoca el `jti` en Redis.
- El refresh usado se revoca antes de emitir el nuevo par.

### 2.3 Clasificación

| Nivel | Orden |
| :--- | ---: |
| `OPEN` | 0 |
| `RESTRICTED` | 1 |
| `CONFIDENTIAL` | 2 |
| `SECRET` | 3 |
| `TOP_SECRET` | 4 |

19 routers declaran mínimo `RESTRICTED` a nivel de router; los handlers elevan el nivel cuando aplica.

### 2.4 Errores

| Código | Significado | Cuerpo |
| ---: | :--- | :--- |
| 400 | Petición inválida / SSRF bloqueado | `{"detail": "..."}` |
| 401 | Token ausente, inválido, expirado o de tipo incorrecto | `{"detail": "..."}` |
| 403 | Clearance insuficiente o recurso ajeno | `{"detail": "..."}` |
| 404 | Recurso inexistente | `{"detail": "..."}` |
| 409 | Conflicto (usuario duplicado) | `{"detail": "..."}` |
| 422 | Validación Pydantic | `{"detail": [...]}` |
| 429 | Rate limit | `{"detail": "..."}` + `Retry-After` |
| 503 | Dependencia caída | `{"detail": "..."}` |

### 2.5 Rate limit

| Cabecera | Significado |
| :--- | :--- |
| `X-RateLimit-Limit` | Límite de la ventana |
| `X-RateLimit-Remaining` | Restante |
| `Retry-After` | Segundos para reintentar (429) |

Límites de borde (Nginx): `auth` 1 r/s, `api` 30 r/s, `burst=100`.

### 2.6 Paginación

**No hay paginación uniforme.** Algunos listados devuelven todos los registros. Es un GAP documentado (R-012). No se debe asumir `limit`/`offset` salvo que el endpoint lo declare.

---

## 3. Endpoints por grupo

La columna «Implementación» resume el veredicto; la evidencia está en `FEATURE_MATRIX.md`.

### 3.1 `/` — REAL

Información de servicio; revela entorno y modelo LLM.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/` | Root | — | REAL |

### 3.2 `/api/v1/aar` — PARCIAL

After Action Review en memoria.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/aar/create` | Create Aar | AAR | PARCIAL |
| GET | `/api/v1/aar/{aar_id}` | Get Aar | AAR | PARCIAL |
| POST | `/api/v1/aar/{aar_id}/finalize` | Finalize Aar | AAR | PARCIAL |
| POST | `/api/v1/aar/{aar_id}/lessons` | Add Lesson Learned | AAR | PARCIAL |
| GET | `/api/v1/aar/{aar_id}/replay` | Get Replay | AAR | PARCIAL |
| POST | `/api/v1/aar/{aar_id}/timeline` | Add Timeline Event | AAR | PARCIAL |

### 3.3 `/api/v1/agents` — STUB

Estado fijo; submódulos devuelven datos mínimos.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/agents/intel/reports` | Get Intel Reports | Agents, Intel | STUB |
| POST | `/api/v1/agents/intel/reports` | Create Intel Report | Agents, Intel | STUB |
| POST | `/api/v1/agents/mesh/broadcast` | Broadcast Message | Agents, Mesh | STUB |
| GET | `/api/v1/agents/mesh/nodes` | Get Mesh Nodes | Agents, Mesh | STUB |
| GET | `/api/v1/agents/mobile/devices` | Get Registered Devices | Agents, Mobile | STUB |
| POST | `/api/v1/agents/mobile/wipe/{device_id}` | Remote Wipe | Agents, Mobile | STUB |
| POST | `/api/v1/agents/multimodal/transcribe` | Transcribe Audio | Agents, Multimodal | STUB |
| POST | `/api/v1/agents/sensors/ingest` | Ingest Reading | Agents, Sensors | STUB |
| POST | `/api/v1/agents/sensors/register` | Register Sensor | Agents, Sensors | STUB |
| GET | `/api/v1/agents/sensors/status` | Mesh Status | Agents, Sensors | STUB |
| GET | `/api/v1/agents/status` | Agent System Status | Agents, SpyManager | STUB |
| POST | `/api/v1/agents/stego/decode` | Stego Decode | Agents, Steganography | STUB |
| POST | `/api/v1/agents/stego/encode` | Stego Encode | Agents, Steganography | STUB |
| GET | `/api/v1/agents/threat/predictions` | Get Threat Predictions | Agents, Threat | STUB |
| GET | `/api/v1/agents/wearable/wearables` | Get Wearable Devices | Agents, Wearable | STUB |
| POST | `/api/v1/agents/wearable/wearables/alert` | Wearable Alert | Agents, Wearable | STUB |

### 3.4 `/api/v1/auth` — REAL

Login, refresh con rotación, logout, me, register.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/auth/login` | Login | Auth | REAL |
| POST | `/api/v1/auth/logout` | Logout | Auth | REAL |
| GET | `/api/v1/auth/me` | Me | Auth | REAL |
| POST | `/api/v1/auth/refresh` | Refresh | Auth | REAL |
| POST | `/api/v1/auth/register` | Register | Auth | REAL |

### 3.5 `/api/v1/c2` — REAL

C2 legacy con DB y servicios; incluye productos/PIR de `v1/intel.py`.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/c2/` | List Assets | C2 | REAL |
| POST | `/api/v1/c2/analyze-threat` | Threat analysis with INTSUM and COAs | C2 | REAL |
| POST | `/api/v1/c2/cyber/alert` | Ingest cyber intelligence alert | C2 | REAL |
| POST | `/api/v1/c2/events/ingest` | Ingest Event | C2 | REAL |
| POST | `/api/v1/c2/fuse` | Fuse multiple intelligence reports | C2 | REAL |
| POST | `/api/v1/c2/generate-coa` | Generate Courses of Action | C2 | REAL |
| POST | `/api/v1/c2/humint/report` | Ingest HUMINT SALUTE report | C2 | REAL |
| POST | `/api/v1/c2/osint/ingest` | Ingest OSINT report | C2 | REAL |
| GET | `/api/v1/c2/pir` | List active Priority Intelligence Requirements | C2 | REAL |
| POST | `/api/v1/c2/pir` | Create Priority Intelligence Requirement | C2 | REAL |
| DELETE | `/api/v1/c2/pir/{pir_id}` | Deactivate a PIR | C2 | REAL |
| GET | `/api/v1/c2/products` | List generated intelligence products | C2 | REAL |
| POST | `/api/v1/c2/products` | Generate an intelligence product | C2 | REAL |
| GET | `/api/v1/c2/products/{product_id}` | Get intelligence product detail | C2 | REAL |
| GET | `/api/v1/c2/query` | Query Timeline | C2 | REAL |
| POST | `/api/v1/c2/query` | Free-form military query | C2 | REAL |
| POST | `/api/v1/c2/register` | Register Asset | C2 | REAL |
| POST | `/api/v1/c2/satellite/ingest` | Ingest satellite imagery product | C2 | REAL |
| POST | `/api/v1/c2/sigint/report` | Ingest SIGINT/COMINT/ELINT report | C2 | REAL |
| GET | `/api/v1/c2/status` | LLM model status | C2 | REAL |
| POST | `/api/v1/c2/strategic-briefing` | Auto-generate strategic briefing | C2 | REAL |
| POST | `/api/v1/c2/{alert_id}/validate` | Validate Alert | C2 | REAL |
| GET | `/api/v1/c2/{id}` | Get Asset | C2 | REAL |

### 3.6 `/api/v1/fusion` — REAL

Motor JDL L0-L4 heurístico.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/fusion/assess-threats` | Assess Threats | Fusion | REAL |
| POST | `/api/v1/fusion/ctp` | Generate Ctp | Fusion | REAL |
| POST | `/api/v1/fusion/intentions` | Evaluate Intentions | Fusion | REAL |
| POST | `/api/v1/fusion/relationships` | Identify Relationships | Fusion | REAL |

### 3.7 `/api/v1/health` — REAL

Probe de salud.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/health` | Health | Health | REAL |

### 3.8 `/api/v1/intel` — STUB

Devuelve listas vacías y estado fijo.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/intel/feeds` | List Intel Feeds | Intelligence, Global-Intel | STUB |
| GET | `/api/v1/intel/reports` | List Intel Reports | Intelligence, Global-Intel | STUB |
| GET | `/api/v1/intel/status` | Intel Status | Intelligence, Global-Intel | STUB |

### 3.9 `/api/v1/logistics` — PARCIAL

Servicio logístico en memoria.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/logistics/delivery` | Register Delivery | Logistics v1 | PARCIAL |
| POST | `/api/v1/logistics/maintenance` | Report Maintenance | Logistics v1 | PARCIAL |
| POST | `/api/v1/logistics/medevac` | Create Medevac | Logistics v1 | PARCIAL |
| GET | `/api/v1/logistics/personnel` | Get Personnel | Logistics v1 | PARCIAL |
| POST | `/api/v1/logistics/request` | Request Supply | Logistics v1 | PARCIAL |
| GET | `/api/v1/logistics/status` | Get Supply Status | Logistics v1 | PARCIAL |
| GET | `/api/v1/logistics/supplies` | Get Supplies | Logistics v1 | PARCIAL |

### 3.10 `/api/v1/map` — REAL

Cálculos geométricos tácticos.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/map/comm-range` | Calculate Comm Range | Tactical Map | REAL |
| POST | `/api/v1/map/engagement-zone` | Calculate Engagement Zone | Tactical Map | REAL |
| GET | `/api/v1/map/layers` | Get Layers | Tactical Map | REAL |
| GET | `/api/v1/map/overlay` | Get Overlays | Tactical Map | REAL |
| POST | `/api/v1/map/overlay` | Add Overlay | Tactical Map | REAL |
| DELETE | `/api/v1/map/overlay/{overlay_id}` | Remove Overlay | Tactical Map | REAL |
| GET | `/api/v1/map/state` | Get Map State | Tactical Map | REAL |
| POST | `/api/v1/map/track` | Track Unit | Tactical Map | REAL |
| GET | `/api/v1/map/unit/{unit_id}/history` | Get Unit History | Tactical Map | REAL |

### 3.11 `/api/v1/messaging` — PARCIAL

Mensajería en memoria; sin persistencia.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/messaging/broadcast` | Broadcast Message | Messaging | PARCIAL |
| GET | `/api/v1/messaging/history` | Get History | Messaging | PARCIAL |
| GET | `/api/v1/messaging/inbox` | Get Inbox | Messaging | PARCIAL |
| POST | `/api/v1/messaging/send` | Send Message | Messaging | PARCIAL |
| DELETE | `/api/v1/messaging/{message_id}` | Delete Message | Messaging | PARCIAL |
| PUT | `/api/v1/messaging/{message_id}/ack` | Acknowledge Message | Messaging | PARCIAL |

### 3.12 `/api/v1/osint` — STUB

Devuelve listas vacías y estado fijo; el dominio vive en `services/osint` sin API.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/osint/cases` | List Cases | OSINT, Atalaya | STUB |
| GET | `/api/v1/osint/entities` | List Entities | OSINT, Atalaya | STUB |
| GET | `/api/v1/osint/health` | Osint Health | OSINT, Atalaya | STUB |
| GET | `/api/v1/osint/jobs` | List Jobs | OSINT, Atalaya | STUB |
| GET | `/api/v1/osint/reports` | List Reports | OSINT, Atalaya | STUB |
| GET | `/api/v1/osint/status` | Osint Status | OSINT, Atalaya | STUB |

### 3.13 `/api/v1/planning` — REAL

OPORD enriquecido en memoria.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/planning/coa-compare` | Compare Coa | Planning | REAL |
| POST | `/api/v1/planning/create` | Create Opord | Planning | REAL |
| GET | `/api/v1/planning/{opord_id}` | Get Opord | Planning | REAL |
| POST | `/api/v1/planning/{opord_id}/annex` | Add Annex | Planning | REAL |
| POST | `/api/v1/planning/{opord_id}/approve` | Approve Opord | Planning | REAL |
| POST | `/api/v1/planning/{opord_id}/distribute` | Distribute Opord | Planning | REAL |
| POST | `/api/v1/planning/{opord_id}/fragord` | Generate Fragord | Planning | REAL |
| PUT | `/api/v1/planning/{opord_id}/paragraph/{paragraph}` | Update Paragraph | Planning | REAL |
| GET | `/api/v1/planning/{opord_id}/risk-assessment` | Risk Assessment | Planning | REAL |
| GET | `/api/v1/planning/{opord_id}/sync-matrix` | Get Sync Matrix | Planning | REAL |
| GET | `/api/v1/planning/{opord_id}/validate` | Validate Opord | Planning | REAL |

### 3.14 `/api/v1/prediction` — REAL

Kalman + patrones + DB.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/prediction/detect-anomalies` | Detect Anomalies | Prediction | REAL |
| POST | `/api/v1/prediction/early-warning` | Early Warning | Prediction | REAL |
| POST | `/api/v1/prediction/pattern-of-life` | Analyze Pattern Of Life | Prediction | REAL |
| POST | `/api/v1/prediction/predict-movement` | Predict Movement | Prediction | REAL |
| GET | `/api/v1/prediction/threat-trend` | Threat Trend | Prediction | REAL |

### 3.15 `/api/v1/reports` — PARCIAL

Reportes en memoria.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/reports` | List Reports | Reports | PARCIAL |
| POST | `/api/v1/reports/medevac` | Generate Medevac Report | Reports | PARCIAL |
| POST | `/api/v1/reports/salute` | Generate Salute | Reports | PARCIAL |
| POST | `/api/v1/reports/sitrep` | Generate Sitrep | Reports | PARCIAL |
| POST | `/api/v1/reports/spotrep` | Generate Spotrep | Reports | PARCIAL |
| GET | `/api/v1/reports/{report_id}` | Get Report | Reports | PARCIAL |

### 3.16 `/api/v1/satellite` — STUB

`/analyze` responde `queued`; no ejecuta análisis.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/satellite/analyze` | Analyze Satellite | Satellite, AEGIS-IMINT | STUB |
| GET | `/api/v1/satellite/status` | Satellite Status | Satellite, AEGIS-IMINT | STUB |

### 3.17 `/api/v1/tactical` — REAL

Delega en servicios tácticos (OPORD, BDA, fires, PSYOPS, wargaming).

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/tactical/bda/assess` | Assess Bda | Tactical, BDA | REAL |
| POST | `/api/v1/tactical/bda/consolidated` | Consolidated Bda | Tactical, BDA | REAL |
| POST | `/api/v1/tactical/bda/satellite` | Satellite Bda | Tactical, BDA | REAL |
| POST | `/api/v1/tactical/fires/assess` | Assess Collateral | Tactical, Joint Fires | REAL |
| POST | `/api/v1/tactical/fires/coordinate` | Coordinate | Tactical, Joint Fires | REAL |
| POST | `/api/v1/tactical/fires/deconflict` | Deconflict | Tactical, Joint Fires | REAL |
| POST | `/api/v1/tactical/opord/fragord` | Generate Fragord | Tactical, OPORD | REAL |
| POST | `/api/v1/tactical/opord/generate` | Generate Opord | Tactical, OPORD | REAL |
| GET | `/api/v1/tactical/opord/{opord_id}` | Get Opord | Tactical, OPORD | REAL |
| POST | `/api/v1/tactical/opord/{opord_id}/validate` | Validate Opord | Tactical, OPORD | REAL |
| POST | `/api/v1/tactical/psyops/campaign` | Plan Campaign | Tactical, PSYOPS | REAL |
| POST | `/api/v1/tactical/psyops/deception` | Generate Deception | Tactical, PSYOPS | REAL |
| POST | `/api/v1/tactical/psyops/message` | Generate Psyops Message | Tactical, PSYOPS | REAL |
| POST | `/api/v1/tactical/wargaming/compare` | Compare Coas | Tactical, Wargaming | REAL |
| POST | `/api/v1/tactical/wargaming/montecarlo` | Monte Carlo | Tactical, Wargaming | REAL |
| POST | `/api/v1/tactical/wargaming/simulate` | Simulate Coa | Tactical, Wargaming | REAL |

### 3.18 `/api/v1/terrain` — REAL

Open Elevation + caché.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v1/terrain/elevation` | Get Elevation | Terrain | REAL |
| POST | `/api/v1/terrain/line-of-sight` | Line Of Sight | Terrain | REAL |
| POST | `/api/v1/terrain/obstacle-detection` | Detect Obstacles | Terrain | REAL |
| POST | `/api/v1/terrain/route-analysis` | Route Analysis | Terrain | REAL |
| POST | `/api/v1/terrain/terrain-analysis` | Terrain Analysis | Terrain | REAL |

### 3.19 `/api/v1/voice` — PARCIAL

Servicio de comandos de voz.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/voice/command` | Process Voice Command | Voice | PARCIAL |
| GET | `/api/v1/voice/status` | Get Voice Status | Voice | PARCIAL |
| POST | `/api/v1/voice/train` | Train Voice Model | Voice | PARCIAL |

### 3.20 `/api/v2/border` — REAL

Persistencia en DB y publicación de eventos.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v2/border/adiz-violation` | Report Adiz Violation | Border, Border / ADIZ | REAL |
| POST | `/api/v2/border/maritime-interdiction` | Initiate Maritime Interdiction | Border, Maritime / Operations | REAL |
| GET | `/api/v2/border/maritime-tracks` | Get Maritime Tracks | Border, Maritime / AIS | REAL |
| POST | `/api/v2/border/perimeter-sensor` | Report Perimeter Event | Border, Border / Sensors | REAL |
| GET | `/api/v2/border/perimeter-status` | Get Perimeter Status | Border, Border / Status | REAL |

### 3.21 `/api/v2/c2` — REAL

Misiones, ORBAT, blue force, órdenes con DB.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v2/c2/blue-force/active` | Get Active Blue Force | C2 v2, C2 / Blue Force | REAL |
| POST | `/api/v2/c2/blue-force/report` | Report Blue Force | C2 v2, C2 / Blue Force | REAL |
| GET | `/api/v2/c2/missions` | List Missions | C2 v2, C2 / Missions | REAL |
| POST | `/api/v2/c2/missions` | Create Mission | C2 v2, C2 / Missions | REAL |
| PUT | `/api/v2/c2/missions/{mission_id}/status` | Update Mission Status | C2 v2, C2 / Missions | REAL |
| GET | `/api/v2/c2/orbat` | Get Orbat | C2 v2, C2 / ORBAT | REAL |
| POST | `/api/v2/c2/orbat/units` | Create Orbat Unit | C2 v2, C2 / ORBAT | REAL |
| POST | `/api/v2/c2/orders` | Issue Order | C2 v2, C2 / Orders | REAL |

### 3.22 `/api/v2/cyber` — REAL

Incidentes, contención, kill chain, threat hunt con DB.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v2/cyber/incidents` | List Cyber Incidents | Cyber, Cyber / Incidents | REAL |
| POST | `/api/v2/cyber/incidents` | Create Cyber Incident | Cyber, Cyber / Incidents | REAL |
| PUT | `/api/v2/cyber/incidents/{incident_id}/contain` | Contain Incident | Cyber, Cyber / Response | REAL |
| GET | `/api/v2/cyber/kill-chain/{incident_id}` | Get Kill Chain Status | Cyber, Cyber / Kill Chain | REAL |
| POST | `/api/v2/cyber/threat-hunt` | Start Threat Hunt | Cyber, Cyber / Threat Hunting | REAL |

### 3.23 `/api/v2/ew` — REAL

Jamming, scans, emisores con DB.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v2/ew/jamming/activate` | Activate Jamming | EW, EW / Jamming | REAL |
| GET | `/api/v2/ew/scans` | List Rf Scans | EW, EW / Spectrum | REAL |
| POST | `/api/v2/ew/scans` | Report Rf Scan | EW, EW / Spectrum | REAL |
| GET | `/api/v2/ew/threat-emitters` | Get Threat Emitters | EW, EW / Threats | REAL |

### 3.24 `/api/v2/logistics` — REAL

Suministros, personal, medevac con DB.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v2/logistics/medevac` | Request Medevac | Logistics, Logistics / Medical | REAL |
| GET | `/api/v2/logistics/personnel` | Get Personnel Status | Logistics, Logistics / Personnel | REAL |
| GET | `/api/v2/logistics/supplies` | List Supplies | Logistics, Logistics / Supplies | REAL |
| POST | `/api/v2/logistics/supplies` | Add Supply | Logistics, Logistics / Supplies | REAL |
| PUT | `/api/v2/logistics/supplies/{supply_id}/consume` | Consume Supply | Logistics, Logistics / Supplies | REAL |

### 3.25 `/api/v2/space` — REAL

Tracking, SSA, ASAT, anomalías con DB.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v2/space/asat-response` | Initiate Asat Response | Space, Space / ASAT | REAL |
| POST | `/api/v2/space/satellites/anomaly` | Report Satellite Anomaly | Space, Space / Anomalies | REAL |
| GET | `/api/v2/space/satellites/tracking` | Get Satellite Tracking | Space, Space / Satellites | REAL |
| GET | `/api/v2/space/space-situational-awareness` | Get Ssa Status | Space, Space / SSA | REAL |

### 3.26 `/api/v3/coa` — REAL

Motor COA: generación, riesgo, armas, comparación.

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v3/coa/assess-risk` | Assess Risk | COA v3 | REAL |
| POST | `/api/v3/coa/compare` | Compare Coas | COA v3 | REAL |
| POST | `/api/v3/coa/generate` | Generate Coas | COA v3 | REAL |
| GET | `/api/v3/coa/templates` | Get Templates | COA v3 | REAL |
| POST | `/api/v3/coa/weapon-availability` | Weapon Availability | COA v3 | REAL |

### 3.27 `/api/v3/fusion` — PARCIAL

—

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| GET | `/api/v3/fusion/cop` | Get Cop | Maven, Maven | PARCIAL |
| POST | `/api/v3/fusion/ingest-event` | Ingest Event | Maven, Maven | PARCIAL |
| GET | `/api/v3/fusion/jdl-pipeline` | Jdl Pipeline Endpoint | Maven, Maven | PARCIAL |

### 3.28 `/api/v3/vision` — PARCIAL

—

| Método | Path | Resumen | Tags | Implementación |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v3/vision/analyze-satellite` | Analyze Satellite | Maven, Maven | PARCIAL |
| POST | `/api/v3/vision/detect-changes` | Detect Changes | Maven, Maven | PARCIAL |
| POST | `/api/v3/vision/drone-frame` | Drone Frame | Maven, Maven | PARCIAL |

---

## 4. Flujos de autenticación

### 4.1 Login

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"<ADMIN_INITIAL_PASSWORD>"}'
```

Respuesta 200:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

### 4.2 Refresh

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<jwt>"}'
```

El refresh usado queda revocado. Reutilizarlo devuelve 401.

### 4.3 Logout

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/logout \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<refresh>"}'
```

### 4.4 Identidad

```bash
curl -s http://localhost:8000/api/v1/auth/me -H 'Authorization: Bearer <access>'
```

### 4.5 Registro

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"operador1","email":"op1@example.mil","password":"<fuerte>"}'
```

El usuario se crea inactivo; un administrador lo activa.

> **MFA OSINT/Intel:** los endpoints `/api/v1/osint/auth/*` y `/api/v1/intel/auth/*` **no están montados** en la app actual. Si un cliente los busca en OpenAPI, no los encontrará. Ver §5.1.

---

## 5. Estado real por grupo (drift)

### 5.1 No montado

| Componente | Ubicación | Rutas que expondría | Estado |
| :--- | :--- | :--- | :--- |
| Media | `backend/app/api/v1/media.py` | `POST /upload`, `PUT /upload/{id}/{filename}` | MUERTO |
| Auth OSINT | `backend/app/api/osint/auth.py` | login, MFA setup/verify, brute force | NO MONTADO |
| Auth Intel | `backend/app/api/intel/auth.py` | TOTP L3, rutas clasificadas | NO MONTADO |
| Admin/países/contributors Intel | `backend/app/api/intel/*.py` | administración, catálogos | NO MONTADO |

Comprobación:

```bash
cd backend
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 - <<'EOF'
from app.main import app
print("media", any("media" in r.path for r in app.routes if hasattr(r, "methods")))
print("osint/auth", any("osint/auth" in r.path for r in app.routes if hasattr(r, "methods")))
print("intel/auth", any("intel/auth" in r.path for r in app.routes if hasattr(r, "methods")))
EOF
# media False
# osint/auth False
# intel/auth False
```

### 5.2 Stubs

| Grupo | Paths | Respuesta | Impacto |
| :--- | ---: | :--- | :--- |
| `/api/v1/osint` | 6 | `{"cases": [], "total": 0}`, estado fijo | Casos/entidades/jobs no existen |
| `/api/v1/intel` | 3 | `{"reports": [], "total": 0}` | Feeds/informes no existen |
| `/api/v1/satellite` | 2 | `{"status": "queued"}` | No hay análisis |
| `/api/v1/agents` | 15 | estado fijo / respuestas mínimas | Mesh, wearable, stego no operan |

### 5.3 Servicios sin API

| Servicio | LOC | API montada |
| :--- | ---: | :--- |
| `services/osint` | 3.136 | 6 rutas stub |
| `services/satellite` | — | 2 rutas stub |
| `services/intel` | — | 3 rutas stub |
| `services/agents` | — | rutas stub |

---

## 6. Matriz de autorización (resumen)

| Grupo | Público | Auth | Clearance mínimo | Test |
| :--- | :---: | :---: | :--- | :--- |
| `/` | Sí | No | — | — |
| `/api/v1/health` | Sí | No | — | `test_v1_clearance_matrix.py` |
| `/api/v1/auth/*` | Login/refresh/register | Me/logout | — | `test_auth.py` |
| `/api/v1/c2/*` | No | Sí | RESTRICTED (handler) | introspección |
| `/api/v1/tactical/*` | No | Sí | RESTRICTED router | introspección |
| `/api/v1/planning/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/map/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/logistics/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/messaging/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/aar/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/reports/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/fusion/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/prediction/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/terrain/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/voice/*` | No | Sí | RESTRICTED handler | introspección |
| `/api/v1/osint/*` | No | Sí | RESTRICTED router | introspección |
| `/api/v1/intel/*` | No | Sí | RESTRICTED router | introspección |
| `/api/v1/satellite/*` | No | Sí | RESTRICTED router | introspección |
| `/api/v1/agents/*` | No | Sí | RESTRICTED router | introspección |
| `/api/v2/*` | No | Sí | RESTRICTED handler | **sin matriz** (GAP) |
| `/api/v3/*` | No | Sí | RESTRICTED router | introspección |
| `/metrics` | **Sí** | No | — | **GAP** |

Resultado del test de introspección: **141 rutas** `/api/v1` + `/api/v3`, **0 gaps**, excluyendo health y auth por diseño.

Comando:

```bash
SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest backend/tests/test_v1_clearance_matrix.py -q
# 5 passed
```

---

## 7. Ejemplos operativos

### 7.1 Health

```bash
curl -s http://localhost:8000/api/v1/health
```

### 7.2 Métricas

```bash
curl -s http://localhost:8000/metrics | head
```

### 7.3 Activos C2

```bash
curl -s http://localhost:8000/api/v1/c2/ \
  -H 'Authorization: Bearer <access>'
```

### 7.4 Productos de inteligencia (C2)

```bash
curl -s http://localhost:8000/api/v1/c2/products \
  -H 'Authorization: Bearer <access>'
```

### 7.5 OPORD táctico

```bash
curl -s -X POST http://localhost:8000/api/v1/tactical/opord/generate \
  -H 'Authorization: Bearer <access>' \
  -H 'Content-Type: application/json' \
  -d '{"mission":"Recon del valle","classification":"SECRET"}'
```

> Los cuerpos exactos dependen de cada modelo Pydantic. Consulte `/openapi.json` para el esquema, no este documento, que sólo fija la ruta y el método.

---

## 8. Contrato y drift

| Comprobación | Comando | Resultado |
| :--- | :--- | :--- |
| Paths del contrato | `python3 -c "import json;print(len(json.load(open('backend/contracts/openapi.json'))['paths']))"` | 168 |
| Paths vivos | introspección `app.routes` | 173 únicos |
| v1 en app viva | `test_contract_v1_paths_in_live_app` | PASS |
| Rutas mínimas | `test_app_has_minimum_routes` | PASS |
| Media no expuesto | `test_media_dead_router_not_exposed` | PASS |

### 8.1 Regla de cambio

1. Cambiar el router.
2. Regenerar `backend/contracts/openapi.json`.
3. Ejecutar `pytest backend/tests/test_contracts.py`.
4. Actualizar este documento si cambia un grupo o un veredicto.

---

## 9. Conclusión

El contrato es amplio (168 paths, 177 operaciones) y está bien organizado por versiones. La calidad de implementación es desigual: los dominios C2, táctico, logística, fusión, predicción, terreno, planificación, v2 y COA son reales; OSINT, Intel, Satellite y Agents de primer nivel son stubs; MFA y media no están montados.

La documentación correcta de una API no es la lista de rutas: es la lista de rutas **con su estado de implementación**. Esa es la aportación de este documento frente al anterior.
