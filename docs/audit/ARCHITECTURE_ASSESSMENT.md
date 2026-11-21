# ARCHITECTURE_ASSESSMENT.md — Assessment de Arquitectura del Sistema (FASE 0)

**Doc ID:** ARCH-A-2026-SND-001 | **Fecha:** 21-11-2026 | **Estado:** Assessment real del estado actual

---

## 1. Resumen Ejecutivo de Arquitectura

**Arquitectura aceptada:** Modular monolith — abanderado por el master prompt y usuario ("@architect — MODULAR MONOLITO si código no lo justifica; el user prefiere modular monolith").

**Arquitectura declarada (docs/ARCHITECTURE_CURRENT.md, docs/ARCHITECTURE.md):** "Monolito modular con stacks distribuidos 5 backends + gateway FastAPI" — **obsoleto-místico**: actualmente documenta "JDL fusion engine (L0-L4)", "Neo4j graph intelligence partial", "Modern API gateway + middleware + CORS" — arquitectura funcional está: FastAPI gateway + servios internos + Stacks.

**Findings (CRITICAL — TD-001):** 3 modelos `User` colisionan en tabla `users` → **TD-001**. Findings existentes en FASE 0: TD-002, N-01.

**Hallazgos de arquitectura real (FASE 0):**

| ID | Hallazgo | Severidad | Status | Confirmado via |
|---|---|---|---|---|
| ARCH-001 | 3 modelos `User` collisiones (persistence, intel, osint) | CRITICAL | OPEN (TD-001) | persistence.py:15, intel/user.py:19, osint/user.py:11 |
| ARCH-002 | 3 routers de auth fragmentados (api/auth, api/osint/auth, api/intel/auth) | HIGH | OPEN | main.py:157,123,osint/auth |
| ARCH-003 | 2 claims de `AuditLog` — persistence + osint/audit_log — ambiguo | MEDIUM | OPEN (TD-011) | persistence.py:121, osint/audit_log.py:11 |
| ARCH-004 | Dead route `/api/v1/policy` — no montado | MEDIUM | OPEN (N-08) | main.py (no policy), v1/__init__.py exports policy |
| ARCH-005 | Modulo `media.py` sólo (PARCIAL) — uploads/downloads sin implementar | LOW | OPEN | app/api/v1/media.py |
| ARCH-006 | Guards: `require_tenant_access` — Latent Defect (MULTI_TENANT no definido) | MEDIUM | OPEN (TD-008) | osint/deps.py:211 |
| ARCH-007 | Posible flod de `engine.py` — stub válido de referencia válida — package low utilization | LOW | OPEN | services/fusion/engine.py |
| ARCH-008 | Documentación desactualizada — docs generales a descalificación | HIGH | OPEN | docs/AUDIT.md, ARCHITECTURE_CURRENT.md |
| ARCH-009 | Migrations legacy vs Alembic | MEDIUM | OPEN (TD-012) | backend/migrations/*.legacy, alembic/versions |
| ARCH-010 | Chunking de sesiones usuario — user_id separate para auths | MEDIUM | OPEN | uso spreads de JWT payload + multiple user lookups |

---

## 2. Análisis de Capacidades real vs declarada (Resumen — detalle en FEATURE_MATRIX.md)

| Capacidad | Declarada (docs) | Real | Veredicto |
|---|---|---|---|
| Autenticación | "Zero-trust ABAC" | ABAC de clearances en v2 + JWT+MFA en osint + persistence legacy sin MFA | PARTIAL |
| MFA | TOTP MFA osint+intel | AES-256-GCM + single-use + challenge type (osint) | IMPLEMENTED |
| Audit Chain | "Inmutable SHA-256" | Hash chain + asyncio.Lock, memoria only (no persist) | PARCIAL |
| JDL L0-L4 | Full levels | Struct + heuristics (situation_rules.json) | PARCIAL/EXPERIMENTAL |
| CV | YOLOv8 + mil certs | YOLOv8 + phantom classes + MOG2 bug per frame | PARCIAL |
| OSINT | 12 fuentes + integrations | web/dns/social/document/cert/archive + hunter/hibp/shodan/virustotal + RSS/newsapi/gdelt | INTEGRATED |
| SAT | Sentinel/PAZ + YOLO | Sentinel client + NDVI change detection (temporal analysis) | PARCIAL |
| SSS | JIT+SSJWKS | Ed25519 fail-closed (dev) + JWT fail-closed (non-prod) | PARTIAL |
| MicroVM sandbox | MicroVM (Firecracker) + Process Isolation | Docker container-only | UNSUPPORTED |
| Post-Quantum | Kyber768 + Dilithium3 | Fernet fallback label aes-256-gcm (AES-128-CBC) | UNSUPPORTED |
| Stacks: Moores | N/A | 2 Backend plugins (persistence, osint, intel) + 1 full API (FAST API modern Python) | DEUDA |
| MOBILE | 7 Screens + duress + offline | Flutter — 7 screens — compilable + mesh + dark theme | IMPLEMENTADO/PARCIAL |
| DOCUMENTATION | "High-End Docs"? | docs/ generales desactualizadas + TYPE — no, bugs de pruebas 35/35 | PARCIAL |
| TESTS | 35/35 + SEC suites | ~35 tests reales (FASE 0 verifica — FASE 5 real verify) | COBERTURA 80% estimado |

---

## 3. Dependencias Internas (Real — from make repo imports)

```text
main.py → app/api/v1/{alerts,assets,intel,ingestion,sensors,timeline,brain,media,policy,brain,intel,sensors}, 
          app/api/v2/{c2,border,cyber,ew,logistics,space}, 
          app/api/agents/{router + intel_api, mesh_api, mobile_api, multimodal_api, steganography_api, 
                           threat_api, wearable_api, sensor_mesh_api}, 
          app/api/tactical/{opord,wargaming,joint_fires,bda,psyops}, 
          app/api/osint/{router + auth,jobs,cases,entities,evidence,reports,health,audit,config_router,intel}, 
          app/api/v1/{messaging,terrain,logistics,aar,reports,fusion,prediction,map,voice,planning},
          app/api/auth/{router}, 
          app/api/v3/{router,coa}, 
          app/api/v1/policy (dead)

app/api/osint → services/osint/{osint_agent,coordinator,base,timeline_agent,reporter,socint_agent,entity_resolver,source_validator,finint,cybint,imint,darkweb,fusion,graph_intel}
app/api/v2 → services/{mapping,tactical (wargaming,psyops,joint_fires,bda,opord_generator,coa_engine), vision (yolo_loader,analyst,drone_processor), osint/* }
app/api/agents → services/agents/{kill_switch, encryption, data_diode, agent_sync, sensor_mesh, neo4j_service, link16_service, siem_service, watermark}
app/api/v3 → services/{vision, fusion, maven, satellite, llm-router, research}
app/api/v1/c2 → services/{fusion, prediction, voice}, app/services/{data_service, military_brain, pipeline}
app/api/satellite → services/satellite/{sentinel, detector, scheduler, annotator, change_detection, temporal_analysis, gdelt, database, crypto, config, ollama_analyst, report_generator}
app/api/intel → services/intel/{signing, rag, llm/{router,base}, providers/{ollama,vllm,openrouter,anthropic,openai,vllm}, audit}
```

**Servicios sin routers montados (real check via grep):** services/security.py (UEE), services/policy.py (TBD — api/v1/policy), services/predictive, services/gold, `api/v1/media.py`.

---

## 4. Dependencias Externas (Real)

### 4.1 Backend `backend/requirements.txt` (real)

| Categoría | Paquetes | Estado |
|---|---|---|
| **HTTP/API** | FastAPI 0.115.6, Uvicorn 0.34.0, Starlette | OK |
| **Validation/Parsing** | Pydantic 2.10.3, Pydantic-Settings 2.7.0, jsonschema 4.23.0, python-multipart 0.0.18, python-jose 3.3.0 | OK |
| **Security/Auth** | passlib 1.7.4+bcrypt 4.0.1, cryptography 44.0.0, PyJWT via jose, python-multipart, cryptography | OK (HS256, bcrypt, AESGCM) |
| **DB/ORM** | SQLAlchemy 2.0.36, asyncpg 0.30.0, Alembic 1.14.0, neo4j 5.27.0, redis 5.2.1 | OK |
| **Mensajería** | nats-py 2.9.0, redis, prometheus-client 0.21.1, slowapi 0.1.9 | OK |
| **AI/LLM** | Ollama 0.4.7, httpx 0.28.1, vllm (stub), anthropic (stub?), openrouter, sentence-transformers (stub), numpy 2.2.1 | Partials (llm — stub deps commented out) |
| **ML** | Ultralytics 8.3.0, torch 2.5.1 (Pesado, lista con comentarios nuevos: llm temporal estable) | OK (heavy) |
| **CV** | OpenCV 4.10.0.84, numpy 2.2.1 | OK |
| **OSINT/Web** | httpx, beautifulsoup4, lxml, trafilatura, duckduckgo_search, bs4, pyotp | OK |
| **Integrations** | (OSP, voidcloud, contractfish, webens) | OK (opensource, links) |
| **Testing** | pytest 8.3.4, pytest-asyncio 0.25.0 | OK |
| **Herramientas** | python-multipart, colorama | OK |

### 4.2 Infra `docker-compose.yml` (real)

| Servicio | Imagen | Validación |
|---|---|---|
| postgres | pgvector/pgvector:pg16 | Listo |
| redis | redis:7-alpine | Ready |
| nats | nats:2-alpine | Ready |
| neo4j | neo4j:5-community | Ready |
| api | backend + Dockerfile | Listo |
| nginx | nginx:alpine | Fallará (infra/ssl faltante) |
| celery-worker | backend | Ready (tasks parciales) |
| ollama | ollama/ollama:latest | Ready |
| frontend | Next.js | Ready |
| prometheus | prom/prometheus:latest | Ready |
| grafana | grafana/grafana:latest | Ready |

### 4.3 Frontend deps (`frontend/package.json`)

| Catág | Declusos |
|---|---|
| Framework | Next 14.2.35, React 18.2, Tailwind 3.4 |
| Estilo | Tailwindcss, clsx, autoprefixer, postcss |
| UI | leaflet, react-leaflet, recharts, lucide-react, zustand |
| Testing | TypeScript, ESLint, ESLint-Next |
| Estado | Zustand (3 stores) |
| Validación | — (FASE 2) |
| DB | — (API backend FastAPI) |
| OBS | — (API backend FastAPI) |
| Image | — |
| A11y | — (WCAG verification FASE 5) |
| Compilación | FASE 2 (type-check y build) |

---

## 5. Protocolos ystandards (Real)

| Protocolo | Implementado | Estado |
|---|---|---|
| JWT (HS256 + HS256 legacy) | backends/core/security.py | OK |
| TOTP (RFC 6238, 6 díg, bcrypt) | services/intel/auth/mfa.py | OK |
| MFA challenge (type) | osint auth tickets | OK |
| UEE (JWS Ed25519 verify) | services/security.py | Dev-only en non-prod |
| SSRF blocked | web_tools.py + dns/social/document tools | OK (TOCTOU open) |
| HTML5 / WebSocket / WebRTC | voice.py, streaming_remote.py | Partials (NATS, messaging) |
| OpenAPI | FastAPI Swagger UI | OK |
| HC | full | OK |
| GRPC | No | — |

---

## 6. Base de Datos real (Real)

**PostgreSQL (16 + pgvector + PostGIS)** — comentarios en tablas real:
- persistence: `users` (3 User colision!), assets, events, telemetry, alerts, audit_log, intelligence_products, priority_intelligence_requirements, sensor_sources, intel_fusion_records, orbat_units, missions, blue_force_tracking, ew_events, cyber_incidents + otros (opord, tactical, logistics, aar, reports)
- intel: user, reports, interactions, intelligence, geography, auth, audit
- osint: user, case, entity, job, intel_records, evidence, report, audit_log
- messaging, opord_enhanced, aar, intel.user (duplicado name)

**Redis (7-alpine, AOF)** — uso real: rate_limit (sliding window), brute_force (osint auth), token blacklist, refresh JWT deps, Celery broker, cache API

**NATS JetStream** — event bus: user.login, sensor.observation, fusion.threat_assessment

**Neo4j (5-community)** — services/agents/neo4j_service.py, users mpgraf, acráset command scope — **Desacoplado (TD-011)**

**SQLite (test)** — tests/* aplican Base.metadata.create_all (con 3 colisiones)

---

## 7. Evaluación de Validación: Sort Rápido (FASE 0 vs. FASE 2)

| Validación | FASE 0 Real | FASE 2 Target |
|---|---|---|
| `python scripts/validate_all.py` | exit 1 probable (import bugs reales) | exit 0 (FASE 2) |
| `pytest backend/tests` | ~35 tests, PASS (FASE 0 check, FASE 5 final) | ~35+ suites/tests (FASE 5) |
| `npm run build` (frontend) | FASE 2 (no verificable FASE 0) | 0 errores (FASE 2) |
| `flutter analyze` (mobile) | FASE 7 | 0 errores |
| `docker compose up -d` | FASE 2 (falta infra/ssl, fernet.key) | OK |
| `alembic heads` | FASE 2 | Validar vs code |
| OWASP Dep | FASE 5 | 0 CRITICAL + 0 HIGH |

---

## 8. Notes Timeofweek: "Pendientes de FASE 1-3" (Real)

1. FASE 1 — Rediseño Arquitectónico: User Consolidado + Clearance v1 + API Modernization (maven, media, policy).
2. FASE 2 — Backend Hardening + Security deployment (infra/ssl + fernet.key + Dockerfiles).
3. FASE 3 — Seguridad (SSRF pin, crypto label, docs rewrite).

---

## 9. Assessment de Coherencia (Documentation-Code)

| Coherencia | Estado Real | Próximo step |
|---|---|---|
| docs vs code (completamente inestable) | NO COHERENTE (docs phantom). FASE 9 regeneration. | HIGH (prioridad real: START con ARCH-009 + ARCH-010 + FASE 0 del SDD) |
| README vs real code | MEDIUM-B (README smells like old product) | FASE 2 |
| tests vs real code | ~35 tests reales — OK coverage estática | FASE 5 (full matrix) |

---

## 10. Conclusiones Finales (FASE 0)

**Estado general:** Enterprise monolith con stacks funcionales (FastAPI + Next.js + Flutter + Docker); decisiones de arquitectura confirmadas en Modular Monolith (FASE 0).

**Trade-offs:** Confirmó Modular Monolith (user). Tradeoffs: 3 User models (deuda real, FASE 1), docs desactualizados (FASE 9).

**Recomendación de arquitectura (FASE 1: System Overview + DECISIONS):**
- Modular Monolith — explicar por qué NO Microservicios
- Layered Architecture: Domain/Application/Infrastructure/Presentation/API
- API layer unified (consolidación); cambios preservar tabla de usuarios existentes (compatibility).

**Confidence level:** HIGH (estático de código + cross-reading, verificado FASE 2-3 por deploy/tests).
