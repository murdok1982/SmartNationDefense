# CONTRATOS DE API — Namespace V1 Único (SESIS-FEDERATION)

> Generado REAL desde la app vivo: `cd backend && python3 -c "import json; from app.main import app; json.dump(app.openapi(), open('contracts/openapi.json', 'w'), indent=2)"`
> V1 namespace único: todos los endpoints del contrato están bajo `/api/v1`. Routers v2/v3 (`/api/v2/*`, `/api/v3/*`) no forman parte del contrato de v1.

- **Total paths en contrato (OpenAPI):** 168
- **Endpoints /api/v1 (tabla abajo):** 134

## Tabla v1 — endpoints reales

| Método | Path | Resumen | Tags |
| :--- | :--- | :--- | :--- |
| POST | /api/v1/aar/create | Create Aar | AAR |
| GET | /api/v1/aar/{aar_id} | Get Aar | AAR |
| POST | /api/v1/aar/{aar_id}/finalize | Finalize Aar | AAR |
| POST | /api/v1/aar/{aar_id}/lessons | Add Lesson Learned | AAR |
| GET | /api/v1/aar/{aar_id}/replay | Get Replay | AAR |
| POST | /api/v1/aar/{aar_id}/timeline | Add Timeline Event | AAR |
| GET | /api/v1/agents/intel/reports | Get Intel Reports | Agents, Intel |
| POST | /api/v1/agents/intel/reports | Create Intel Report | Agents, Intel |
| POST | /api/v1/agents/mesh/broadcast | Broadcast Message | Agents, Mesh |
| GET | /api/v1/agents/mesh/nodes | Get Mesh Nodes | Agents, Mesh |
| GET | /api/v1/agents/mobile/devices | Get Registered Devices | Agents, Mobile |
| POST | /api/v1/agents/mobile/wipe/{device_id} | Remote Wipe | Agents, Mobile |
| POST | /api/v1/agents/multimodal/transcribe | Transcribe Audio | Agents, Multimodal |
| POST | /api/v1/agents/sensors/ingest | Ingest Reading | Agents, Sensors |
| POST | /api/v1/agents/sensors/register | Register Sensor | Agents, Sensors |
| GET | /api/v1/agents/sensors/status | Mesh Status | Agents, Sensors |
| GET | /api/v1/agents/status | Agent System Status | Agents, SpyManager |
| POST | /api/v1/agents/stego/decode | Stego Decode | Agents, Steganography |
| POST | /api/v1/agents/stego/encode | Stego Encode | Agents, Steganography |
| GET | /api/v1/agents/threat/predictions | Get Threat Predictions | Agents, Threat |
| GET | /api/v1/agents/wearable/wearables | Get Wearable Devices | Agents, Wearable |
| POST | /api/v1/agents/wearable/wearables/alert | Wearable Alert | Agents, Wearable |
| POST | /api/v1/auth/login | Login | Auth |
| POST | /api/v1/auth/logout | Logout | Auth |
| GET | /api/v1/auth/me | Me | Auth |
| POST | /api/v1/auth/refresh | Refresh | Auth |
| POST | /api/v1/auth/register | Register | Auth |
| GET | /api/v1/c2/ | List Assets | C2 |
| POST | /api/v1/c2/analyze-threat | Threat analysis with INTSUM and COAs | C2 |
| POST | /api/v1/c2/cyber/alert | Ingest cyber intelligence alert | C2 |
| POST | /api/v1/c2/events/ingest | Ingest Event | C2 |
| POST | /api/v1/c2/fuse | Fuse multiple intelligence reports | C2 |
| POST | /api/v1/c2/generate-coa | Generate Courses of Action | C2 |
| POST | /api/v1/c2/humint/report | Ingest HUMINT SALUTE report | C2 |
| POST | /api/v1/c2/osint/ingest | Ingest OSINT report | C2 |
| POST | /api/v1/c2/pir | Create Priority Intelligence Requirement | C2 |
| GET | /api/v1/c2/pir | List active Priority Intelligence Requirements | C2 |
| DELETE | /api/v1/c2/pir/{pir_id} | Deactivate a PIR | C2 |
| GET | /api/v1/c2/products | List generated intelligence products | C2 |
| POST | /api/v1/c2/products | Generate an intelligence product | C2 |
| GET | /api/v1/c2/products/{product_id} | Get intelligence product detail | C2 |
| GET | /api/v1/c2/query | Query Timeline | C2 |
| POST | /api/v1/c2/query | Free-form military query | C2 |
| POST | /api/v1/c2/register | Register Asset | C2 |
| POST | /api/v1/c2/satellite/ingest | Ingest satellite imagery product | C2 |
| POST | /api/v1/c2/sigint/report | Ingest SIGINT/COMINT/ELINT report | C2 |
| GET | /api/v1/c2/status | LLM model status | C2 |
| POST | /api/v1/c2/strategic-briefing | Auto-generate strategic briefing | C2 |
| POST | /api/v1/c2/{alert_id}/validate | Validate Alert | C2 |
| GET | /api/v1/c2/{id} | Get Asset | C2 |
| POST | /api/v1/fusion/assess-threats | Assess Threats | Fusion |
| POST | /api/v1/fusion/ctp | Generate Ctp | Fusion |
| POST | /api/v1/fusion/intentions | Evaluate Intentions | Fusion |
| POST | /api/v1/fusion/relationships | Identify Relationships | Fusion |
| GET | /api/v1/health | Health | Health |
| GET | /api/v1/intel/feeds | List Intel Feeds | Intelligence, Global-Intel |
| GET | /api/v1/intel/reports | List Intel Reports | Intelligence, Global-Intel |
| GET | /api/v1/intel/status | Intel Status | Intelligence, Global-Intel |
| POST | /api/v1/logistics/delivery | Register Delivery | Logistics v1 |
| POST | /api/v1/logistics/maintenance | Report Maintenance | Logistics v1 |
| POST | /api/v1/logistics/medevac | Create Medevac | Logistics v1 |
| GET | /api/v1/logistics/personnel | Get Personnel | Logistics v1 |
| POST | /api/v1/logistics/request | Request Supply | Logistics v1 |
| GET | /api/v1/logistics/status | Get Supply Status | Logistics v1 |
| GET | /api/v1/logistics/supplies | Get Supplies | Logistics v1 |
| POST | /api/v1/map/comm-range | Calculate Comm Range | Tactical Map |
| POST | /api/v1/map/engagement-zone | Calculate Engagement Zone | Tactical Map |
| GET | /api/v1/map/layers | Get Layers | Tactical Map |
| POST | /api/v1/map/overlay | Add Overlay | Tactical Map |
| GET | /api/v1/map/overlay | Get Overlays | Tactical Map |
| DELETE | /api/v1/map/overlay/{overlay_id} | Remove Overlay | Tactical Map |
| GET | /api/v1/map/state | Get Map State | Tactical Map |
| POST | /api/v1/map/track | Track Unit | Tactical Map |
| GET | /api/v1/map/unit/{unit_id}/history | Get Unit History | Tactical Map |
| POST | /api/v1/messaging/broadcast | Broadcast Message | Messaging |
| GET | /api/v1/messaging/history | Get History | Messaging |
| GET | /api/v1/messaging/inbox | Get Inbox | Messaging |
| POST | /api/v1/messaging/send | Send Message | Messaging |
| DELETE | /api/v1/messaging/{message_id} | Delete Message | Messaging |
| PUT | /api/v1/messaging/{message_id}/ack | Acknowledge Message | Messaging |
| GET | /api/v1/osint/cases | List Cases | OSINT, Atalaya |
| GET | /api/v1/osint/entities | List Entities | OSINT, Atalaya |
| GET | /api/v1/osint/health | Osint Health | OSINT, Atalaya |
| GET | /api/v1/osint/jobs | List Jobs | OSINT, Atalaya |
| GET | /api/v1/osint/reports | List Reports | OSINT, Atalaya |
| GET | /api/v1/osint/status | Osint Status | OSINT, Atalaya |
| POST | /api/v1/planning/coa-compare | Compare Coa | Planning |
| POST | /api/v1/planning/create | Create Opord | Planning |
| GET | /api/v1/planning/{opord_id} | Get Opord | Planning |
| POST | /api/v1/planning/{opord_id}/annex | Add Annex | Planning |
| POST | /api/v1/planning/{opord_id}/approve | Approve Opord | Planning |
| POST | /api/v1/planning/{opord_id}/distribute | Distribute Opord | Planning |
| POST | /api/v1/planning/{opord_id}/fragord | Generate Fragord | Planning |
| PUT | /api/v1/planning/{opord_id}/paragraph/{paragraph} | Update Paragraph | Planning |
| GET | /api/v1/planning/{opord_id}/risk-assessment | Risk Assessment | Planning |
| GET | /api/v1/planning/{opord_id}/sync-matrix | Get Sync Matrix | Planning |
| GET | /api/v1/planning/{opord_id}/validate | Validate Opord | Planning |
| POST | /api/v1/prediction/detect-anomalies | Detect Anomalies | Prediction |
| POST | /api/v1/prediction/early-warning | Early Warning | Prediction |
| POST | /api/v1/prediction/pattern-of-life | Analyze Pattern Of Life | Prediction |
| POST | /api/v1/prediction/predict-movement | Predict Movement | Prediction |
| GET | /api/v1/prediction/threat-trend | Threat Trend | Prediction |
| GET | /api/v1/reports | List Reports | Reports |
| POST | /api/v1/reports/medevac | Generate Medevac Report | Reports |
| POST | /api/v1/reports/salute | Generate Salute | Reports |
| POST | /api/v1/reports/sitrep | Generate Sitrep | Reports |
| POST | /api/v1/reports/spotrep | Generate Spotrep | Reports |
| GET | /api/v1/reports/{report_id} | Get Report | Reports |
| POST | /api/v1/satellite/analyze | Analyze Satellite | Satellite, AEGIS-IMINT |
| GET | /api/v1/satellite/status | Satellite Status | Satellite, AEGIS-IMINT |
| POST | /api/v1/tactical/bda/assess | Assess Bda | Tactical, BDA |
| POST | /api/v1/tactical/bda/consolidated | Consolidated Bda | Tactical, BDA |
| POST | /api/v1/tactical/bda/satellite | Satellite Bda | Tactical, BDA |
| POST | /api/v1/tactical/fires/assess | Assess Collateral | Tactical, Joint Fires |
| POST | /api/v1/tactical/fires/coordinate | Coordinate | Tactical, Joint Fires |
| POST | /api/v1/tactical/fires/deconflict | Deconflict | Tactical, Joint Fires |
| POST | /api/v1/tactical/opord/fragord | Generate Fragord | Tactical, OPORD |
| POST | /api/v1/tactical/opord/generate | Generate Opord | Tactical, OPORD |
| GET | /api/v1/tactical/opord/{opord_id} | Get Opord | Tactical, OPORD |
| POST | /api/v1/tactical/opord/{opord_id}/validate | Validate Opord | Tactical, OPORD |
| POST | /api/v1/tactical/psyops/campaign | Plan Campaign | Tactical, PSYOPS |
| POST | /api/v1/tactical/psyops/deception | Generate Deception | Tactical, PSYOPS |
| POST | /api/v1/tactical/psyops/message | Generate Psyops Message | Tactical, PSYOPS |
| POST | /api/v1/tactical/wargaming/compare | Compare Coas | Tactical, Wargaming |
| POST | /api/v1/tactical/wargaming/montecarlo | Monte Carlo | Tactical, Wargaming |
| POST | /api/v1/tactical/wargaming/simulate | Simulate Coa | Tactical, Wargaming |
| GET | /api/v1/terrain/elevation | Get Elevation | Terrain |
| POST | /api/v1/terrain/line-of-sight | Line Of Sight | Terrain |
| POST | /api/v1/terrain/obstacle-detection | Detect Obstacles | Terrain |
| POST | /api/v1/terrain/route-analysis | Route Analysis | Terrain |
| POST | /api/v1/terrain/terrain-analysis | Terrain Analysis | Terrain |
| POST | /api/v1/voice/command | Process Voice Command | Voice |
| GET | /api/v1/voice/status | Get Voice Status | Voice |
| POST | /api/v1/voice/train | Train Voice Model | Voice |

## Drift control

- **Contrato:** `backend/contracts/openapi.json` (OpenAPI generado real de `app.main.app.openapi()`).
- **Test de drift:** `backend/tests/test_contracts.py` — ejecutable real: `cd backend && python3 -m pytest tests/test_contracts.py -q`.
- **Regla:** el contrato `/api/v1` debe ser subset del app vivo; endpoint eliminado de la app sin regenerar contrato → drift FAIL (test falla).
- **Regenerar contrato:** `cd backend && python3 -c "import json; from app.main import app; json.dump(app.openapi(), open('contracts/openapi.json', 'w'), indent=2)"`.
