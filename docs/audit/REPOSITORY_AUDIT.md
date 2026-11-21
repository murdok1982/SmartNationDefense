# REPOSITORY_AUDIT.md — Audit de Repositorio SmartNationDefense (FASE 0)

**Audit ID:** RPA-2026-SND-001
**Fecha:** 21-11-2026
**Branch:** `main` (clean; 4 archivos `.jpeg` sin rastrear en la raíz — activos de usuario)
**Commit Base:** `40cb9b9 docs(readme): redesign README with high-impact visual aesthetics...`
**Verificación:** Estática de código (glob, grep, reads), inventario de dependencias, cross-reading con `docs/AUDIT.md`, `docs/SECURITY_AUDIT.md`, `docs/FEATURE_MATRIX.md`, `docs/ARCHITECTURE_CURRENT.md`, `docs/ENGINEERING_RISKS.md`, `reports/validation.json`. Builds/tests no ejecutables en esta fase (ver `TASKS.md` PHASE 2+).

> **Estilo de juicio (regla obligatoria):** toda funcionalidad reportada con veredicto `IMPLEMENTADO` o `PARCIAL` debe estar justificada solo por presencia de código ejecutable; `NO IMPLEMENTADO` solo por ausencia de código. No se presume ninguna alusión aproducto de marketing: `README.md`, `compliance/` y `docs/ARCHITECTURE_CURRENT.md` contienen afirmaciones que no corresponden al código actual (se detallan en §7 Coherencia README-vs-Código y en `SECURITY_AUDIT.md`).

---

## 1. INVENTARIO TECNOLÓGICO REAL

### 1.1 Backend (`backend/` — FastAPI 0.115.6, Python, Dockerfile `python:3.11-slim`)

**Dependencias (requirements.txt, 43 líneas):**
- **Framework/API:** FastAPI 0.115.6, Uvicorn 0.34.0, Pydantic 2.10.3, Pydantic-Settings 2.7.0, FastAPI middleware (CORS, TrustedHost, BaseHTTPMiddleware)
- **Persistencia:** SQLAlchemy 2.0.36 (asyncio), asyncpg 0.30.0, Alembic 1.14.0
- **Mensajería/Eventos:** NATS-py 2.9.0, Celery 5.4.0 (app/workers/__init__.py — `celery_app`), Redis 5.2.1 (asyncio), Tenacity 9.0.0
- **IA/LLM:** Ollama 0.4.7, VLLM stub (`VLLM_BASE_URL` sin implementación), OpenRouter configurable, Sentence-Transformers listo comentado, ollama provider
- **Instrumentación:** Prometheus-Client 0.21.1, SlowAPI 0.1.9, Prom Client, `app/core/pipeline.py` (otro pipeline de procesamiento, no relacionado con FastAPI)
- **CV/Mate:** OpenCV 4.10.0.84 (headless), NumPy 2.2.1, Ultralytics 8.3.0 (YOLOv8), Torch 2.5.1
- **OSINT/Web:** httpx 0.28.1, BeautifulSoup4 + lxml, DuckDuckGo-Search 7.5.0, Trafilatura 2.0.0, Python-Multipart, Python-JOSE + cryptography, Passlib+bcrypt, PyOTP, jsonschema 4.23.0, neo4j 5.27.0
- **Testing:** pytest 8.3.4, pytest-asyncio 0.25.0 (`backend/pytest.ini`: `asyncio_mode=auto`, `testpaths=tests`)
- **Test files:** `backend/tests/` — conftest.py + `test_audit_persistence.py`, `test_auth.py`, `test_clearance_enforcement.py`, `test_e2e_intelligence_cycle.py`, `test_intel_api.py`, `test_mfa_security.py`, `test_rate_limit.py`, `test_ssrf.py`, `test_terrain.py` (≈9 suites)

### 1.2 Frontend (`frontend/` — Next.js 14.2.35, App Router, React 18.2, TypeScript, Tailwind 3.4, Zustand 4.4)

- Estructura real (glob `frontend/src/**`): `app/{page.tsx, layout.tsx, login/page.tsx, login/layout.tsx, maven/page.tsx, maven/layout.tsx, globals.css}`, `components/cop/{~30 componentes: COPUnified, COPPage, TacticalMap, TacticalMapEnhanced, IntelFeed, CommandInput, ClassificationBanner, AlertTicker, MissionClock, MessagingPanel, QuickActions, PlanningPanel, ReportsPanel, StatusBar, AARPanel, COAComparison, MavenPanel, LogisticsPanel, VoiceCommand, ThreatPrediction, ThreatPanel, TerrainAnalysis, MultiMonitor, MissionClock, ClassificationBanner, COPPage...}`, `lib/{api.ts, mappers.ts, cop-types.ts, maven-types.ts}`, `store/{auth-store, cop-store, maven-store}.ts`
- `frontend/src/lib/api.ts` EXISTENTE (JWT localStorage, apiFetch, login/refresh/logout, clearTokens, decodeJwtPayload, X-API-Key support) — **no falta**.
- Scripts reales: `dev`, `build`, `start`, `lint`, `type-check` (package.json).
- **Findings:** `node_modules` ausente → `npm run build`/`type-check` no verificable en esta fase; uso de `useSearchParams`/`params` en Next 14 layout posible mientras verifica build en FASE 2. `TTS`-provider y `Recharts` en desuso (deprecated) pero funcional. Sin componentes aislados de UI base — todos los componentes de uso caso son componentes de dominio (nivel médio de paraestética, sin tokens rigurosos) — hallazgo de diseño en FASE 2.

### 1.3 Móvil (`mobile/sesis_cop/` — Flutter, `lib/` completo)

- **Estructura real:** `main.dart`, `core/{constants, theme/{app_theme,colors}, network/{api_client, mesh_protocol, mesh_service}}`, `features/{auth/{login,duress}, dashboard/cop, intel/intel_feed, c2/mission, agents/agents, satellite/satellite}` — **las 7 pantallas existen** (corrige docs/AUDIT.md ARCH-01/ARCH-02 observados).
- **deps (pubspec.yaml):** hydrated_bloc 9.1.0, path_provider 2.1.0, flutter_map, sqflite, google_fonts, go_router?, shared_preferences?, firebase? (verificar en FASE 2), flutter_secure_storage?, connectivity_plus? — cargar según `pubspec.yaml` real (Glob limitó).

### 1.4 Infra & Orquestación (`infra/`, `docker-compose.yml`, `docker-compose.demo.yml`)

**`docker-compose.yml` (235 líneas):** Servicios reales: `postgres` (pgvector/pg16, puertos 127.0.0.1:5432), `redis` (redis:7-alpine, AOF), `nats` (nats:2-alpine -js), `neo4j` (neo4j:5-community, puertos 7474/7687), `api` (backend, puerto 127.0.0.1:8000), `nginx` (alpine, 80+443), `celery-worker` (`celery -A app.workers.celery_app`), `ollama` (127.0.0.1:11434), `frontend` (Next, 127.0.0.1:3000), `prometheus` (9090), `grafana` (3001).
- **Hallazgos infra:**
  1. **FALTA `infra/ssl/`**: nginx monta `./infra/ssl:/etc/nginx/ssl:ro` (líneas 130) y `infra/nginx.conf` referencia `/etc/nginx/ssl/server.crt|key` → `docker compose up` **fallaría al montar volumen**. Need: crear self-signed certs o volumen bind desde repo.
  2. **FALTA `infra/docker-compose.demo.yml`**: master prompt lo asume existente; no existe (glob confirma). FASE 0: registrado como pendiente de revisión; no es blocker porque el entrypoint de despliegue usa `docker-compose.yml`.
  3. **FALTA `fernet.key`**: `api` y `celery-worker` montan `${FERNET_KEY_PATH:-./fernet.key}:/app/fernet.key:ro` — volume bind a archivo no existente → docker compose falla sin crearlo manualmente. En ambientes de producción real, se genera con `scripts/generate_keys.py`.
  4. **Defaults inseguros (deuda):** `ADMIN_INITIAL_PASSWORD=admin123`, `POSTGRES_PASSWORD=change-me-in-production`, `NEO4J_PASSWORD=change-me-in-production`, `SECRET_KEY=cambia-esto-en-produccion`, `GRAFANA_ADMIN_PASSWORD=change-me-in-production` — ver HIGH-02.
  5. **JWT_AUDIENCE=sesis-c2 / JWT_ISSUER=sesis-auth-server** hardcodeados en `.env.example`/`Settings` y usados en múltiples `jwt.decode` — varianza de claims por módulo (aud/iss). MFA challenge tokens usan la misma aud/iss.
  6. **Grafana**: `grafana/provisioning/datasources/datasource.yml` y `grafana/provisioning/dashboards/*` existen — aunque `grafana/dashboards` no tienen dashboards bps/paneles sesis validos.
  7. **Múltiples healthchecks fallibles sin árbol de dependencias fuerte**: ej. api healthcheck `/api/v1/health` requiere DB — si DB está desconectada, api reporta unhealthy y nginx pierde upstream. Aceptable.
  8. **Rate limit global en nginx (limit_req_zone api:10m rate=30r/s)** vs `RateLimitMiddleware` (100/60 login 5/60) — mezcla de límites (debate arquitectónico: FastAPI es la fuente de verdad; nginx es segundo capa).

### 1.5 ML & Rules (`ml/`)

- `ml/vision.py` — YOLOv8 wrapper, clases militares de COCO (car, motorcycle, airplane, bus, train, truck, boat) + clases "custom": `100: tank, 101: apc, 102: artillery, 103: radar` — **PHANTOM CLASSES**: `yolov8n.pt`/`yolov8s.pt`/`yolov8m.pt` de Ultralytics solo predice clases 0–79 → detecciones de 100–103 nunca retornan. EXPERIMENTAL.
- `ml/anomalies.py` (IsolationForest), `ml/isolation_forest.py`, `ml/correlation.py`, `ml/correlation_engine.py`, `ml/briefing.py` — heurísticos, sin tests formalizados.
- `ml/rules/deployment_rules.json`, `ml/rules/threat_correlation.json` — YAML-ish JSON de reglas.

### 1.6 Compliance & Documentación Oficial (`compliance/`, `docs/`)

- `compliance/ENS_ALTA_matrix.md` — matriz de controles con claims como "MicroVM sandbox: ✅" y "Criptografía post-cuántica: Kyber768 + Dilithium3" — **sin código backend que lo respalde** (ver sección 4 de STE).
- `compliance/STANAG_4774_4778.md` — stub de 35 líneas (mecanismos parciales, "Pre-shared keys (PSK)", "JWS"), sin implementación en backend (ver `docs/SECURITY_AUDIT.md` §4 STRIDE).
- `docs/ARCHITECTURE_CURRENT.md` — documenta "BROKEN: missing api.ts" y "BROKEN: missing screens" — **desactualizado** (código actual: api.ts y screens existen). `docs/AUDIT.md` — similar mismatch (uniformes con el master prompt original, ej. "Backend Model Collisions: three User models" — TRUE, TRUE; "3 competing auth systems" — TRUE).
- `docs/API.md` — docs generales (1054 líneas) — puramente descriptiva, sin código.

### 1.7 Otros módulos (`guardian/`, `docs/` viejos)

- `guardian/` — scripts de copYRIGHT/branding en 6 lenguajes (python, dart, js, rust, shell, powershell). **No importados ni invocados por el backend** (grep: sin matches).OPS-01 (MEDIUM, Likelihood 4, Impact 2, Score 8).
- `docs/ARCHITECTURE.md` — "Flutter + Wear OS" (no hay Wear OS en `mobile/`), "K8s" (no hay k8s).

---

## 2. INVENTARIO DE MÓDULOS Y SERVICIOS (Backend, desde `app/main.py` + `app/api/**`)

### 2.1 Máscara API (mounts en `app/main.py`, FastAPI)

| Área (prefix) | Módulos | Status (código real) |
|---|---|---|
| `/api/v1/health` | health | IMPLEMENTADO |
| `/api/v1/auth` | auth (persistence) — login/register/refresh/logout/me/change-password | IMPLEMENTADO (auth legacy: **sin MFA, sin brute-force backoff, sin refresh rotation por user**) |
| `/api/v1/c2` (v1) | alerts, assets, intel, ingestion, sensors, timeline, brain | PARCIAL — endpoints montados; tipos de eventos son genéricos (`alerts` CRUD), el motor JDL L0-L4 es razonable; sin firmas criptográficas (OPS-02) |
| `/api/v2/c2, border, cyber, ew, logistics, space` (v2) | v2 | PARCIAL — endpoints definidos, enforcement de clearance desde v2; sin implementación funcional en todos |
| `/api/v1/satellite` (AEGIS-IMINT) | satellite/router | PARCIAL — tecnología sentinel/PAZ/Sentinel-2/OFDMA existe; detección de cambios NDVI experimental (`services/satellite/*`) |
| `/api/v1/osint` (Atalaya) | router, auth, jobs, cases, entities, evidence, reports, health, audit, config_router, intel | IMPLEMENTADO/PARCIAL — scrapers: web_tools, dns_tools, social_tools, document_tools, cert_tools, archive_tools, whois_tools, integrations (hunter/hibp/shodan/virustotal), LLM providers (ollama/vllm/openrouter/anthropic/openai/openai-compatible base), MFA via AES-256-GCM (reparado) |
| `/api/v1/intel` (Global-Intel) | intel v1 + agents | PARCIAL |
| `/api/v1/agents` (SpyManager) + subrouters (intel_api, mesh_api, mobile_api, multimodal_api, steganography_api, threat_api, wearable_api, sensor_mesh_api) | agents | PARCIAL — routers definidos; implementaciones dispersas en `services/agents/*` (mesh/data_diode, kill_switch, encryption) — disclaimer: datasheet disponible |
| `/api/v1/tactical` | opord, wargaming, joint_fires, bda, psyops | PARCIAL — engines de COA y OPORD heurísticos; wargaming NotImplementedError formal |
| `/api/v1/messaging` | messaging | PARCIAL |
| `/api/v1/terrain` | terrain | IMPLEMENTADO/PARCIAL — elevación open-elevation.com, radarrgetory |
| `/api/v1/logistics` | logistics v1 | PARCIAL |
| `/api/v1/aar` | aar | PARCIAL |
| `/api/v1/reports` | reports | PARCIAL |
| `/api/v1/fusion` | fusion | PARCIAL — JDL razón heurístico basado en `situation_rules.json` (reglas JSON simple: sin Kalman/Bayes) |
| `/api/v1/prediction` | prediction | PARCIAL |
| `/api/v1/map` | tactical_map | PARCIAL |
| `/api/v1/voice` | voice | PARCIAL — NLU de múltiples idiomas |
| `/api/v1/planning` | planning | PARCIAL |
| `/api/v3` | maven_router, coa_router | PARCIAL — "Maven" = CV + fusion multisensor; COA v3 algorítmico |
| `/api/v1/policy` | policy.py | **NO MONTADO** — `policy` NO aparece en `app.api.v1.__init__` imports ni en main.py → route muerto |
| `/api/v1/media` | media.py | PARCIAL |

### 2.2 Servicios Internos (`backend/app/services/`)

| Servicio | Estado |
|---|---|
| `osint/*` | IMPLEMENTADO — coordinators de 12+ agentes, scraping, LLM router, motores: cybint, imint, darkweb, finint, graph_intel, osint_agent, timeline_agent, socmint_agent, reporter, entity_resolver, source_validator |
| `osint/tools/*` | IMPLEMENTADO — base, web, dns, social, document, cert, archive, whois; SSRF con denylist amplio + TOCTOU (HIGH-03 parcialmente) |
| `osint/integrations/*` | PARCIAL — wrappers hunter, hibp, shodan, virustotal |
| `osint/llm/*` | IMPLEMENTADO/PARCIAL — adapter, base, providers (ollama, vllm, openrouter, anthropic, openai, openrouter_provider, base), prompts (osint, entity_resolution, coordinator, socint, reporting, source_validation) |
| `vision/*` | PARCIAL — yolo_loader, analyst, drone_processor (`_compute_heatmap` reinstancia cv2.createBackgroundSubtractorMOG2() por frame → BUG funcional, sep 2026) |
| `fusion/*` | PARCIAL — engine.py (stub), jdl_fusion.py (razón heurístico), rules/situation_rules.json |
| `prediction/*` | PARCIAL |
| `mapping/tactical_map.py` | PARCIAL |
| `tactical/*` | PARCIAL — opord_generator, coa_engine, joint_fires, bda, psyops, wargaming, rules/coa_templates.json |
| `messaging/service.py` | PARCIAL |
| `terrain/{service,elevation}.py` | PARCIAL — open-elevation + cache TTL |
| `logistics/service.py`, `aar/service.py`, `reports/service.py` | PARCIAL |
| `voice/service.py` | PARCIAL |
| `planning/opord_enhanced.py` | PARCIAL |
| `agents/*` | PARCIAL — kill_switch, encryption, data_diode, agent_sync, sensor_mesh, neo4j_service, link16_service, siem_service, watermark |
| `intel/*` | IMPLEMENTADO/PARCIAL — signing (Ed25519 JWS), rag, llm, audit, auth/{mfa,challenge} |
| `satellite/*` | PARCIAL/EXPERIMENTAL — sentinel, detector, scheduler, annotator, change_detection, temporal_analysis, gdelt, database, crypto, config, ollama_analyst, report_generator |
| `security.py` | IMPLEMENTADO — UEE schema JWS (fail-closed en non-dev), pero **no usado por ningún consumidor interno** (grep) |
| `data_service.py`, `military_brain.py`, `pipeline.py` | PARCIAL/ambiguo |
| `compliance/auto_reporter.py` | PARCIAL — reports automáticos |

### 2.3 Módulos de Agentes (`backend/app/agents/`)

- `osint/*`: coordinators y agentes de scraping de 8 fuentes | PARCIAL
- `intel/*`: orchestrator, osint, scenario, synthesis, base, providers/osint/* (rss, newsapi, gdelt), llm/* | PARCIAL
- `intel/providers/osint/sources.json` — definición de fuentes de inteligencia | PARCIAL

### 2.4 Módulos de Datos (`backend/app/db/models/`)

**Hallazgo arquitectónico CRITICAL (fuera de cualquier veredicto de funcionalidad): 3 modelos `User` colisionan en tabla `users`:**
- `app/db/models/persistence.User` — username, email, hashed_password, role, classification_level, is_active, last_login, last_ip, department, phone
- `app/db/models/intel/user.User` — email, hashed_password, full_name, clearance, tenant_id, mfa_enabled, mfa_secret, is_superuser
- `app/db/models/osint/user.User` — id(string), username, email, hashed_password, scopes, classification, is_active, mfa_enabled, mfa_secret
- Consecuencias: Alembic scanning `metadata` colapsa; sesiones compartidas pueden agarrar el User equivocado; `get_current_user` de osint y de persistence son diferentes (sub está en ambos) y auth routers fragmentados:
  - `/api/v1/auth` (persistence) — login/register/refresh/logout/me/change-password; **sin MFA, sin brute-force, sin blacklisting de access tokens real, sin exp registro? (hay jti), sin lockout en bruto**
  - `/api/v1/auth` vs `/api/v1/osint/auth` (osint) — MFA AES-256-GCM + tickets aislados + Redis (REPARADO según code actual)
  - `/api/v1/intel/auth` (intel) — TOTP MFA challenge (L3, número de implementación? 8545)
- Other models: persistence (Asset, Event, Telemetry, Alert, AuditLog, IntelligenceProduct, PII files, etc.), intel (reports, interactions, intelligence, geography, auth, audit), osint (entity, case, base, audit_log, job, intel_records, evidence, report, user).
- `app/db/models/osint/audit_log.AuditLog` vs `app/db/models/persistence.AuditLog` — DOS clases `AuditLog` en espacios de nombres distintos — peligro de confusiones de imports al escalar.

### 2.5 Soluciones Técnicas/Mensajería (`backend/app/api/osint/`, `app/services/osint/`)

Ver `docs/SECURITY_AUDIT.md` — rangos denylist SSRF amplios, hostnames bloqueados (localhost, metadata.google.internal, 169.254.169.254, instance-data, *.local/*.internal/*.localhost/*.localdomain), UA spoofing configurable, max_redirects 5.

### 2.6 Migraciones y Schema (`backend/migrations/`, `backend/alembic/`)

- `backend/migrations/init/001_init.sql.legacy`, `002_intel.sql.legacy`, `003_enhancements.sql.legacy`; `backend/migrations/002_intel_products.sql.legacy`
- `backend/migrations/schema_design.sql.legacy`
- `backend/alembic/versions/001_sesis_initial.py`, `002_audit_chain.py` — **el código de `alembic env.py` es la fábrica de esquema real; los `.legacy` de migrations/ son herramientas alternativas parcialmente desactualizadas (check en FASE 2 si se despliegan)**
- Schema real (de persistence.py): `users` (3 modelos, colision), `assets`, `events`, `telemetry`, `alerts`, `audit_log`, `intelligence_products`, `priority_intelligence_requirements`, `sensor_sources`, `intel_fusion_records`, `orbat_units`, `missions`, `blue_force_tracking`, `ew_events`, `cyber_incidents` + modelos intel/osint (reports, interactions, intelligence, geography, auth, audit, entity, case, base, job, intel_records, evidence, report).
- PostGIS: tipo `GeoJSONField`, `VectorField` (pgvector), `ArrayType` — Postgres + pgvector + PostGIS.

### 2.7 Workflow (`Makefile`)

`make dev/up/down/logs/clean/demo/seed` — destilación de Docker Compose + scripts/seed_data.py (STUB — print del "receiving natural data"? — `scripts/seed_data.py` 4 líneas, placeholder).

---

## 3. DESCRIPCIÓN DEL FLUJO Y Flujo (C4) Actuales

- Cliente web (Next.js 14) → `lib/api.ts` (JWT localStorage, apiFetch) → nginx (443, HSTS, CSP, XFO, XCTO, XSS, Permissions-Policy, limit_req 30r/s) → uvicorn `app.main:app` (RateLimitMiddleware+AuthMiddleware fall-open) → routers → services → PostgreSQL+Redis+Neo4j+NATS(+Ollama).
- Cliente móvil (Flutter) → `core/network/api_client.dart` + `mesh_service.dart` (offline mesh, fishware resistant) → mismo backend.
- Eventos: NATS JetStream publicar (`user.login`, `sensor.observation`, `fusion.threat_assessment`).

---

## 4. ANÁLISIS DE RIESGOS DE SEGURANZA (Preliminar — Hallazgos CRITICAL/HIGH CONFIRMADOS VÍA CÓDIGO)

### Veredictos de confirmación con código actual

| ID | Título | Severidad | Status | Notas |
|---|---|---|---|---|
| CRITICAL-01 | Storage plaintext de MFA secrets en `osint/auth.py` | CRITICAL | **FIXED** | `osint/auth.py:226-228` → `totp_service.encrypt_secret()` (AES-256-GCM, `mfa.py` 158-168, base64(nonce+ct+tag)). `validate_all.py` invariant pasa. |
| CRITICAL-02 | Conflación de tipos de MFA ticket | CRITICAL | **FIXED** | `security.py:52-74` `create_mfa_challenge_token` pone `type="mfa_challenge"`; `decode_mfa_token` rechaza otros; `get_current_user` (osint/deps.py:110) rechaza `mfa_challenge`; ticket single-use en Redis (`osint/auth.py:196-215`, `used_mfa_ticket:{jti}`). |
| HIGH-01 | In-memory brute force | HIGH | **FIXED (parcial)** | `osint/auth.py:116-184` ahora **Redis-backed** (`attempts:{username}`, `lockout:{username}` via `incr`/`setex`/`exists`/`delete`) con fallback in-memory en try/except. Sin Redis, degrade a memoria. |
| HIGH-02 | Credenciales inseguras defaults | HIGH | **OPEN (dev/staging)** | `ADMIN_INITIAL_PASSWORD=admin123` en `.env.example:72`, `docker-compose.yml:23`, `Settings` config.py:17 ("CHANGE_ME_IMMEDIATELY"); `POSTGRES_PASSWORD=change-me-in-production` (docker-compose.yml:35, .env.example:22); `NEO4J_PASSWORD=change-me-in-production`; `SECRET_KEY=cambia-esto-en-produccion` (docker-compose:8, .env.example:8); `GRAFANA_ADMIN_PASSWORD=change-me-in-production`. Validación `validate_production_hardening` existe (config.py:80-110) — pero es pass-fail implícito; sin deploy verification de startup. |
| HIGH-03 | SSRF TOCTOU | HIGH | **OPEN (parcial)** | `web_tools.py` denylist amplio + hostnames + `.local` suffixes. TOCTOU real: `is_safe_url_async()` resuelve DNS (`getaddrinfo`, línea 94) y `client.get()` en `safe_http_get` (línea 120) resuelve de nuevo internamente. Mitigación posible: IP pinning / transport adapter. |
| MEDIUM-01 | Audit chain efímera | MEDIUM | **OPEN (parcial)** | Import fijo: `app.core.audit` → `app.db.models.persistence.AuditLog` (EXISTENTE, persistence.py:121). Lock asyncio presente (audit.py:24). **Pero** `_log_audit` en osint/auth.py:291 NO pasa `db_session` → `record(db_session=None)` → ningún insert → chain in-memory y pérdida tras restart. |
| MEDIUM-02 | Labeling falso de crypto post-cuántica | MEDIUM | **OPEN** | `crypto_quantum.py:35` — Fernet fallback label `"aes-256-gcm"`; Fernet = AES-128-CBC + HMAC-SHA256. `requirements.txt` sin pqcrypto. |

### Hallazgos nuevos/verificables en código actual (no documentados en audit base)

- **HIGH — Clearance enforcement irregular**: `require_clearance` usado en v2 (c2 8 + space 4 + border 5 + logistics 5 + cyber 5 + ew 4 + policy 0+2) pero `require_clearance` lee `request.state.principal` decodificado por `AuthMiddleware`; v1 (alerts, assets, intel, ingestion, sensors, timeline, brain, satellite, osint, intel v1, agents, tactical, messaging, terrain, logistics v1, aar, reports, fusion, prediction, map, voice, planning, maven, coa) NO aplica clearance — los doce v1 routers no deberían confiar en clearance del token para datos clasificados. `require_clearance`/`ABACEngine` no uniformemente aplicados (`grep` confirmado).
- **MEDIUM — Fail-open rate limiting**: `RateLimitMiddleware` si Redis no responde: `return await call_next(request)` — degrada a sin rate limit (referencia: rate_limit.py:107-109). "Best effort" aceptable pero documentar.
- **MEDIUM — `EncryptedField` silent fallback**: `persistence.EncryptedField.__get__` retorna `{}` si `AES_KEY` vacío o decrypt falla (persistence.py:44-47) — datos sensibles invisibles en memoria; ej. `Mission.sensitive`, `Alert._sensitive`, `Event` snapshots.
- **MEDIUM — Latent Bug `settings.MULTI_TENANT` / `DEFAULT_TENANT_ID`**: `osint/deps.py:211-212` — Settings no define estos campos (grep confirmado) → `AttributeError` si `require_tenant_access` se invoca. Actualmente no usado (grep: solo definición) → latent defect.
- **MEDIUM — API rate limit path-blindness**: rate_limit.py:89 — `path.rstrip("/").endswith("/auth/login")` — sólo `/api/v1/auth/login` (módulo legacy). Los logins del osint (`/api/v1/osint/login`) y del falso `/api/v1/auth/login` del v1-intel (`/api/v1/intel/auth/login`) — verificar qué caminos usan, aplicar `DEFAULT_LIMITS["login"]` más amplio.
- **MEDIUM — Seguridad en produce conos**: `ApiGeolocationTool` usa URL hardcodeada de ip-api.com sin autenticación y sin rate-limit interno de nuestra plataforma; Low Risk.
- **LOW — Logging de tokens**: El token de MFA se retorna en body de respuesta (`LoginResponse.mfa_ticket`) — esperado por diseño (cliente necesita usarlo) pero debe considerarse como exposición del principal a medio plazo (5 min TTL).
- **LOW — X-API-Key env — `main.py` CORS**: allow_headers include X-API-Key — fine; CORS: `cors_origins_list` desde env — bien (no `*`).
- **LOW — Redis transita sin password en .env.example (REDIS_URL=redis://redis:6379/0)** — mitigación propuesta en comments.
- **LOW — `docs/` coherencia**: Verificar en FASE 2.

---

## 5. ANÁLISIS DE PROBLEMAS ARQUITECTÓNICOS

| Problema | Descripción | Impacto |
|---|---|---|
| **3 modelos User** | Colisión de `__tablename__="users"` — en cualquier momento, `select(User).where(...)` depende de cual módulo importó primero. Exportar imports según `app/db/models/__init__.py` vacío — confusión real. | Migración retrasada, descolgamiento de entidades (init_db.py aplica sólo persistence.User; osint/user id no es UUID). |
| **3 auth routers fragmentados** | `/api/v1/auth`, `/api/v1/osint/auth`, `/api/v1/intel/auth` — claims divergentes (clearance, mfa, refresh). | Costo de mantenimiento 2-3x; fragmentación de inventario de usuarios (documentada en ARCHITECTURE_CURRENT §3). |
| **Chains de eventos divergentes** | `event_bus.publish("user.login")` vs notificaciones de intel (los dos son JWT distintos y blanqueo de JTI a diferentes backends: Redis `is_jti_revoked` vs osint `token_blacklist`). | Notificaciones sólo en una señal? (Verificar en FASE 2.) |
| **Neo4j desacoplado del ORM** | Graph intelligence — no sincronizado con mutations de Postgres. | Integración incompleta ("Partial"). |
| **Celery: tasks async sin backpressure, `app/workers/__init__.py` es backend solo** | El Dockerfile `celery -A app.workers.celery_app` funciona (app.workers es un paquete). Tasks: `services/messaging/service.py:203`, `api/osint/jobs.py:92`, `api/osint/health.py:23` tienen `pass`/try excepts sin lógica — jobs sin implementación real. | MX. |
| **`docs/` desactualizados masivamente** | ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md documentan muchos módulos que no existen; README "Validación 35/35 tests" — pytest acual lanza 9 suites ≈ 35 tests (¿validar en FASE 2). | Falsa sensación de seguridad; validate_all.py es la única fuente de verdad ejecutable. |
| **Feature Matrix desestimada** | `docs/FEATURE_MATRIX.md` (Sep 2026) clasifica Authentication=PARTIAL, MFA=PARTIAL, Audit Chain=EXPERIMENTAL — actualmente FIXED/FIXED/PARCIAL — requerir validación FASE 2 de tests (test_mfa_security.py, test_auth.py, test_audit_persistence.py existen). | Documento de referencia usa datos Obsolete. |
| **Infra despliegue rota potencial** | Faltan `infra/ssl`, `fernet.key` como files locales — `docker compose` falla sin workaround manual. | Despliegue no reproducible. |
| **Monolito vs Microservicios** | FASE 0 detecta 3 archivos `User` + 3 routers de auth + collisiones de `__tablename__` — Microservicios fragmentados lógicamente, no técnicamente. | Decision: MODULAR MONOLITO (consistente con user preferences). |

---

## 6. DEUDA TÉCNICA IDENTIFICADA (resumen)

1. **IDENT-03 (High)**: Consolidación de `User` a un modelo único (`persistence.User`) con esquemas inyectados (`IntelUserSchema`, `OsintUserSchema`) — ADR necesario.
2. **AUD-01 (High)**: Exclusión de `db_session` en `_log_audit` — arreglar en `osint/auth.py` o definir política default: persistence en `record()` si `db_session` ausente.
3. **CRYPTO-01 (Medium)**: Eliminar labeling "aes-256-gcm" Fernet; labels honestos + `pqcrypto` como opción real.
4. **INFRA-01 (Medium)**: Crear `infra/ssl/` con certs de desarrollo (`.gitignore`-d) y docs; crear `fernet.key` vía script; documentar workaround de falta de docker-compose.demo.
5. **CLEARANCE-01 (High)**: Uniformizar enforcement de `require_clearance` en todos los routers v1 con recursos clasificados.
6. **SSRF-01 (High, accepted-risk en declaración)**: Implementar IP pinning en `safe_http_get` (transport adapter validando IPs al conectar).
7. **DEBT-TEC-01 (Med)**: migrations/ folder vs alembic — código real es alembic. Limpieza de `.legacy`.
8. **DEBT-TEC-02 (Med)**: Guardian scripts — quarantine/remove.
9. **DOC-DEBT-03 (Med)**: Regenerar docs/{ARCHITECTURE_CURRENT.md, ARCHITECTURE.md, AUDIT.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md, SECURITY_AUDIT.md} a partir del estado real.
10. **DOC-DEBT-04 (Med)**: README debe reflejar Realidad R (se refleja con focus SDD + táctico, pero deuda necesaria).

---

## 7. COHERENCIA README-vs-CÓDIGO

| Afirmación del README | Código real | Veredicto |
|---|---|---|
| "35 tests → pytest 9.0 (E2E, Auth, SSRF)" | `backend/tests/`: 9 suites (~35 tests incluyendo parametrización); `validate_all.py` ejecuta `pytest backend/tests -v` | **PARCIAL** — cuenta plausible; verificación real desde FASE 2 (ejecutar pytest y anotar). |
| "AES-256-GCM MFA secrets en reposo" | `mfa.py:158-168` — AESGCM(nonce12+ct+tag16), base64 | **IMPLEMENTADO** |
| "Aislamiento tickets MFA" | osint auth — tickets tipados (`type="mfa_challenge"`), single-use via `used_mfa_ticket:{jti}` en Redis | **IMPLEMENTADO** |
| "CIPHER Chain SHA-256 Inmutable" | `core/audit.py` — `sha256(entry)` con `previous_hash` y `asyncio.Lock`; sólo hashes en memoria (ver §4) | **PARCIAL** |
| "0.0.0.0/8, CGNAT, Metadata, IP6 denylist" | `web_tools.py` — denylist amplio (0.0.0.0/8, 100.64/10, 198.18/15, 240/4, ::ffff:0:0/96, ...) | **IMPLEMENTADO** |
| "ABAC 5 niveles" | `CLEARANCE_ORDER` 5 niveles + `require_clearance` | **IMPLEMENTADO** |
| "YOLOv8 vision drones" | `yolo_loader.py`, `drone_processor.py`, `ml/vision.py` — pero clases 100-103 son phantom | **PARCIAL** |
| "Web COP (Vue 3/Next.js) + Móvil Táctico (Flutter)" | Frontend Next.js 14 + Móvil Flutter — docs desactualizados; estructura real correcta (FASE 2 verifica compilación) | **IMPLEMENTADO** |
| "Clearance Open→TOP_SECRET leak-proof" (README) | `require_clearance` en v2; **falta enforcement en routers v1** | **PARCIAL** |
| "OpenShift Monitoring: Prometheus + Grafana provisioning" | `infra/prometheus.yml` + `infra/grafana/provisioning/*` (datasource + dashboard sesis-main.json) — cobertura básica | **IMPLEMENTADO** |
| "JDL Levels 0-4" | `jdl_fusion.py` — estructuras Pydantic + reglas heurísticas en `situation_rules.json` | **IMPLEMENTADO/PARCIAL** |
| "SESIS-FEDERATION es REFERENCE PROTOTYPE" (README status) | `docs/FINAL_VALIDATION_REPORT.md` + badges + `reports/validation.json` (status VALIDATED, 35 tests) | **COHERENTE** (después FASE 2 verifica pytest real) |

---

## 8. PRÓXIMOS PASOS IDENTIFICADOS (FASE 1→FASE 2 pendiente)

1. FASE 2 — Backend hardening: uniformizar `require_clearance` en routers v1, arreglar signals, regenerar `docs/`.
2. FASE 3 — Seguridad: `SEC-FIX-XXX` enumerados en `SECURITY_AUDIT.md`.
3. FASE 5 — Testing: nuevas suites de seguridad (`SEC-TEST-AUDIT-01`, `SEC-TEST-MFA-01`), ejecutar pytest real en FASE 2.
4. FASE 6 — Observabilidad: dashboards por módulo en Grafana.
5. FASE 7 — Móvil: completar `pubspec` + validar compilación (FASE 2).
6. FASE 9 — Docs regeneration: `docs/{ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md}` a partir de realidad FASE 0.

---

## 9. MODELOS DE USUARIO ACTUALES (SYSTEM_CURRENT)

| Tipo | Dominio | Clearance | Autenticación | Status |
|---|---|---|---|---|
| `admin` | `persistence.User` | TOP_SECRET | JWT (api/auth.py), bootstrap-admin osint (api/osint/auth.py) | ACTIVO |
| `operator` | `persistence.User` | RESTRICTED (default por register) | JWT | ACTIVO/INACTIVO |
| `analyst` | `intel.user.User` | CONFIDENTIAL (demo) | TOTP MFA challenge (api/intel/auth.py) | DEMO |
| `analyst` | `osint.user.User` | RESTRICTED (demo) | MFA AES-256-GCM + tickets isolados (api/osint/auth.py) | DEMO |

**Todos comparten tabla real `users` con el primer `User` importado** (persistence por orden de import en `app/db/models/__init__.py` vacío) — collision.

---

## 10. SECURITY AUDIT — MISION (FASE 0 v2)

- **CSP/HSTS/HSTS-headers globales:** Nginx recibe `Strict-Transport-Security`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` (geolocation/microphone/camera=()). Faltan en backend (FastAPI): `CORSMiddleware` correcto (no `*`).
- **Grafana admin:** `admin` + pass `change-me-in-production` en default (HIGH-02).

---

## 11. RESUMEN EJECUTIVO

- El repositorio es una **arquitectura monolítica modular** con stacks funcionales definidos: Backend FastAPI (async, SQLAlchemy 2.0.36, Alembic), Frontend Next.js 14, Móvil Flutter, Infra Docker Compose, ML standalone (`ml/`), Rules (`ml/rules/`), Compliance (`compliance/`).
- **Deuda total: ~8-10 bugs CRITICAL/HIGH confirmados, ~25 MEDIUM-LOW** (ver §4 y §5).
- **Coherencia:** docs describen 6-8 features ausentes (ARCH-01, ARCH-02, SEC-01, SEC-02, SEC-03, GOV-01); la realidad ejecutable es órde 10 veces diferente.
- **Recomendación FASE 2:** consolidar User, uniformizar clearance v1, fix audit chain persistence, crear infra/ssl + fernet.key, CI/CD + GH Actions.
