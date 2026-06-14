# SESIS-FEDERATION Architecture

## Overview
Monorepo unifying 5 military-grade intelligence platforms with 19 integrated modules.

## Directory Structure
```
backend/         - FastAPI + Celery workers
  app/api/v1/    - messaging, fusion, terrain, logistics, aar, reports, prediction, map, voice, planning
  app/api/v2/    - multi-domain ops (border, c2, cyber, ew, logistics, space)
  app/api/tactical/ - opord, wargaming, joint_fires, bda, psyops
  app/services/  - Business logic per module
frontend/        - Next.js 14 dashboard
mobile/          - Flutter + Wear OS
ml/              - Anomaly detection, vision, correlation
scripts/         - Deployment utilities
infra/           - Nginx, Prometheus, Grafana, K8s
docs/            - Architecture, API, SOPs
compliance/      - STANAG, ENS, NIST matrices
```

## Core Services
1. **Fusion Engine** — central orchestrator
2. **fsociety LLM** — unified AI brain
3. **Event Bus (NATS)** — C2/telemetry
4. **Audit Chain** — immutable SHA-256
5. **ABAC** — attribute-based access control

## Module Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SESIS-FEDERATION C4ISR                         │
│           Plataforma Unificada de Gobierno Digital Militar          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
     ┌────────┬────────┬────────┬────────┬────────┬────────┐
     │        │        │        │        │        │        │
┌────┴───┐┌───┴───┐┌───┴───┐┌───┴───┐┌───┴───┐┌───┴───┐┌──┴────┐
│SESIS   ││AEGIS  ││Atalaya││Global ││SpyMgr ││Mobile ││Tacti- │
│(C2)    ││(SAT)  ││(OSINT)││(Intel)││(Agents││(Flutt)││cal    │
└────────┘└───────┘└───────┘└───────┘└───────┘└───────┘└───────┘
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     │                            │                            │
┌────┴─────────┐  ┌──────────────┴──────────┐  ┌─────────────┴────┐
│  NUEVOS      │  │  FUSION & ANALYSIS      │  │  PLANNING &      │
│  MODULOS     │  │                         │  │  REPORTING       │
│              │  │  - JDL Level 2 Fusion   │  │                  │
│ - Messaging  │  │  - Threat Prediction    │  │ - OPORD NATO 5   │
│   (QoS)      │  │  - Terrain Analysis     │  │   Paragraphs     │
│ - Logistics  │  │  - Pattern of Life      │  │ - AAR System     │
│ - Voice Cmd  │  │  - Early Warning        │  │ - Auto Reports   │
│ - Tac. Map   │  │                         │  │   (SITREP/       │
│              │  │                         │  │    SPOTREP/       │
│              │  │                         │  │    SALUTE)        │
└──────────────┘  └─────────────────────────┘  └──────────────────┘
```

## JDL Level 2 Fusion Architecture

The Joint Directors of Laboratories (JDL) Level 2 fusion engine performs **situation assessment** by refining entity-level observations into a comprehensive tactical picture.

```
┌──────────────────────────────────────────────────────┐
│              JDL FUSION ENGINE                       │
│                                                      │
│  INPUTS                    PROCESSING                │
│  ───────                   ──────────                │
│  Satellite Detections  ──► Threat Assessment         │
│  OSINT Events          ──► Relationship Analysis     │
│  Sensor Readings       ──► Intention Evaluation      │
│  Agent Reports         ──► CTP Generation            │
│                                                      │
│  OUTPUTS                                             │
│  ───────                                             │
│  - Hostile/Friendly/Neutral entity classification    │
│  - Relationship graph (command, support, subord.)    │
│  - Predicted enemy intentions with confidence        │
│  - Threat zones with severity levels                 │
│  - Recommended actions with priorities               │
│  - Common Tactical Picture (CTP) consolidated        │
└──────────────────────────────────────────────────────┘
```

### JDL Fusion Endpoints

| Endpoint | Function |
|----------|----------|
| `POST /api/v1/fusion/assess-threats` | Classify entities and assess threat level |
| `POST /api/v1/fusion/relationships` | Identify relationships between entities |
| `POST /api/v1/fusion/intentions` | Predict enemy intentions with indicators |
| `POST /api/v1/fusion/ctp` | Generate Common Tactical Picture |

## Tactical Messaging Architecture

Military-grade messaging with Quality of Service (QoS) levels following NATO STANAG standards.

```
┌──────────────────────────────────────────────────────┐
│           TACTICAL MESSAGING SYSTEM                  │
│                                                      │
│  QoS LEVELS (highest to lowest priority):            │
│  ────────────────────────────────────────             │
│  FLASH    → Immediate delivery, preemptive           │
│  IMMEDIATE → High priority, expedited delivery       │
│  PRIORITY  → Standard military priority              │
│  ROUTINE   → Normal delivery queue                   │
│                                                      │
│  FEATURES                                            │
│  ────────                                            │
│  - E2E encryption (AES-256-GCM)                     │
│  - Digital signatures (Ed25519)                      │
│  - STANAG classification labels                      │
│  - Thread support with parent references             │
│  - TTL (Time-To-Live) for message expiry            │
│  - Acknowledgment tracking                           │
│  - Broadcast to multiple recipients                  │
└──────────────────────────────────────────────────────┘
```

### Messaging Endpoints

| Endpoint | Function |
|----------|----------|
| `POST /api/v1/messaging/send` | Send message with QoS priority |
| `GET /api/v1/messaging/inbox` | Get inbox with filters |
| `POST /api/v1/messaging/broadcast` | Broadcast to multiple recipients |
| `GET /api/v1/messaging/history` | Get message history |
| `PUT /api/v1/messaging/{id}/ack` | Acknowledge message receipt |
| `DELETE /api/v1/messaging/{id}` | Delete message |

## ML Threat Prediction Architecture

Machine learning pipeline for predicting enemy movements and detecting anomalies.

```
┌──────────────────────────────────────────────────────┐
│           THREAT PREDICTION ENGINE                   │
│                                                      │
│  INPUTS                    MODELS                    │
│  ───────                   ──────                    │
│  Unit positions/speed  ──► Movement Prediction       │
│  Event streams         ──► Anomaly Detection         │
│  Historical patterns   ──► Pattern of Life (PoL)     │
│  Friendly locations    ──► Early Warning System      │
│                                                      │
│  OUTPUTS                                             │
│  ───────                                             │
│  - Predicted future positions with confidence        │
│  - Anomaly scores for event streams                  │
│  - Pattern of Life deviations                        │
│  - Early warning alerts with threat radius           │
│  - Movement trajectory projections                   │
└──────────────────────────────────────────────────────┘
```

### Prediction Endpoints

| Endpoint | Function |
|----------|----------|
| `POST /api/v1/prediction/predict-movement` | Predict unit future position |
| `POST /api/v1/prediction/detect-anomalies` | Detect anomalies in events |
| `POST /api/v1/prediction/pattern-of-life` | Analyze unit pattern of life |
| `POST /api/v1/prediction/early-warning` | Generate early warning alerts |

## New Modules Summary

| # | Module | Service | Key Capabilities |
|---|--------|---------|-----------------|
| 10 | sesis-messaging | `messaging/service.py` | QoS military messaging, E2E encryption, threads, TTL |
| 11 | sesis-fusion | `fusion/jdl_fusion.py` | JDL Level 2 situation assessment, CTP generation |
| 12 | sesis-terrain | `terrain/service.py` | LOS, route planning, elevation, obstacle detection |
| 13 | sesis-logistics | `logistics/service.py` | Supplies, personnel, MEDEVAC 9-line, maintenance |
| 14 | sesis-aar | `aar/service.py` | After Action Review, timeline, lessons learned, replay |
| 15 | sesis-reports | `reports/service.py` | SITREP, SPOTREP, SALUTE, MEDEVAC report generation |
| 16 | sesis-prediction | `prediction/threat_prediction.py` | Movement prediction, anomaly detection, PoL, early warning |
| 17 | sesis-mapping | `mapping/tactical_map.py` | Multi-layer overlays, unit tracking, engagement zones, comm ranges |
| 18 | sesis-voice | `voice/service.py` | Voice/text command processing, multi-language NLU |
| 19 | sesis-planning | `planning/opord_enhanced.py` | OPORD 5 paragraphs NATO, FRAGORD, COA comparison, risk assessment |

