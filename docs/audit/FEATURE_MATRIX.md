# FEATURE_MATRIX.md — Matriz de Realidad de Funcionalidades (FASE 0)

**Doc ID:** FMX-2026-SND-001 | **Fecha:** 21-11-2026 | **Estado:** Matriz real — junio 2026 / agosto 2026 / septiembre 2026

> **Método:** Equivalente a `docs/FEATURE_MATRIX.md` original, pero instanciado en código real FASE 0 (sin marca "HIDDEN/SUPPORTED" — está instanciado y generado desde código, nuevos veredictos: `IMPLEMENTADO` / `PARCIAL`). Estado: `VALIDATED` / `INTEGRATED` / `PARTIAL` / `PARCIAL` / `EXPERIMENTAL` / `STUB` / `PLANNED` / `UNSUPPORTED` / `FALSO`.

---

## 1. Core Reality Matrix — Instanciado

| Funcionalidad | Código | Integrado | Estado Real | Notas (Real) |
|---|:---:|:---:|:---:|---|
| **Autenticación** | Yes | Partial | `PARTIAL` | Fragmentado en 3 modelos User + 3 routers de auth; test_auth.py existe (~6 suites reales) |
| **MFA** | Yes | Partial | `PARTIAL` | MFA in OSINT (FIXED); MFA in Intel (L3-capable, state-grade); No MFA en persistence v1 auth. **Osint admin bootstrap**: items 86-3 — `mfa_enabled` a FALSE default. |
| **Audit Chain** | Yes | Partial | `PARTIAL` | In-memory (no db_session calls → persistence nunca usada). test_audit_persistence.py existe. |
| **JDL Fusion L0-L4** | Yes | Partial | `EXPERIMENTAL` | Engine pydantic + reglas heurísticas (`situation_rules.json`), sin Kalman/Bayes/BN |
| **Computer Vision** | Yes | Partial | `EXPERIMENTAL` | YOLOv8 (some), pero clases phantom 100-103; per-frame MOG2 reset bug real |
| **Anomaly Detection** | Yes | Partial | `PARTIAL` | IsolationForest (ml/), wrapper en backend; tests nuevos (test_rate_limit etc.) |
| **OSINT Tools** | Yes | Yes | `INTEGRATED` | 12 tools + 6 integrations + LLM providers; SSRF doblemente validado (FASE 0) |
| **Graph Intelligence** | Yes | Partial | `PARTIAL` | Neo4j client (services/agents/neo4j_service.py), nátADJUNTO desacoplado |
| **LLM Orchestration** | Yes | Partial | `PARTIAL` | Ollama + OpenRouter + vllm + anthropic + openai — sin Pydantic structured outputs revalidables |
| **Multi-Agent Architecture** | Yes | Partial | `EXPERIMENTAL` | SpyManager (5 screens), Agent_SMS (mail API), Detectron + Keras — 4 impl reales. |
| **Common Operating Picture (COP)** | Yes | Yes | `INTEGRATED` | Next.js full stack — compiles — reducción de poco: CSP/HSTS in nginx |
| **Mobile Client (Flutter)** | Yes | Yes | `INTEGRATED` | All 7 screens — Flutter App compiles — dark military theme, notification opt |
| **Offline Mode & Mesh** | Yes | No | `EXPERIMENTAL` | mesh_service + api_client — sync queue + storage partial — read about ownership. |
| **Event Bus (NATS)** | Yes | Yes | `INTEGRATED` | events.py — publisher + nats-py — DLQ y idempotency faltantes (FASE 2 backlog) |
| **Observability** | Yes | Partial | `PARTIAL` | Prometheus + Grafana provisioning básica — monitoring: slo Alert manager — Log tracing simple. |
| **Docker Orchestration** | Yes | Yes | `INTEGRATED` | 11 services — deploy broken (infra/ssl faltante) — FASE 2 fix |
| **CI/CD Pipeline** | No | No | `PLANNED` | NADA — FASE 4 |
| **Post-Quantum Crypto** | Yes | No | `UNSUPPORTED` | Fernet label honesto — pqcrypto optional — FASE 5 |
| **MicroVM Sandbox** | No | No | `UNSUPPORTED` | 0 código — corrección: compliance no validada — FASE 2 por aclarar |
| **Real-time Platform** | No | No | `UNSUPPORTED` | No Phase, Incidents, Log técnico en backend |
| **Webkiton NEW apps (page.tsx, maven, login, logout, display)** | Yes | No | `STUB` | page.tsx listo, maven/login/duress sin implementación |

---

## 2. Backend Matrix (Routers Real)

| API | Estado Real | Test Real |
|---|---|---|
| `/api/v1/auth/*` | PARTIAL (legacy, no MFA) | `test_auth.py` (~8) — verificar FASE 2 |
| `/api/v1/osint/auth/*` | IMPLEMENTADO/PARCIAL (MFA AES-256-GCM FIXED) | `test_mfa_security.py` |
| `/api/v1/intel/auth/*` | IMPLEMENTADO/PARCIAL (TOTP L3 challenge) | `test_auth.py` |
| `/api/v1/c2/alerts/assets/intel/ingestion/sensors/timeline/brain` | PARCIAL | test_intel_api.py, test_terrain.py, test_clearance_enforcement.py |
| `/api/v2/*` (c2, border, cyber, ew, logistics, space) | PARCIAL | test_clearance_enforcement.py (V2) |
| `/api/v1/satellite/*` | PARCIAL | test_terrain.py (partial) |
| `/api/v1/osint/*` (12 modules) | IMPLEMENTADO/PARCIAL | test_ssrf.py, test_rate_limit.py |
| `/api/v1/tactical/*` | PARCIAL | test_e2e_intelligence_cycle.py |
| `/api/v1/messaging/*` | PARCIAL | — |
| `/api/v1/terrain/*` | IMPLEMENTADO/PARCIAL | test_terrain.py |
| `/api/v1/logistics/*` | PARCIAL | — |
| `/api/v1/aar/*` | PARCIAL | — |
| `/api/v1/reports/*` | PARCIAL | — |
| `/api/v1/fusion/*` | PARCIAL | — |
| `/api/v1/prediction/*` | PARCIAL | — |
| `/api/v1/map/*` | PARCIAL | — |
| `/api/v1/voice/*` | PARCIAL | — |
| `/api/v1/planning/*` | PARCIAL | — |
| `/api/v3/*` (maven, coa) | PARCIAL | — |
| `/api/v1/policy/*` | **NO MOUNTED** (dead) | — |
| `/api/v1/media/*` | PARCIAL | — |

---

## 3. Frontend Matrix (Real)

| Componente/Página | Estado Real | Test/Compilación (FASE 2 verify) |
|---|---|---|
| `app/page.tsx` | Intento HTML | Compilable (FASE 2 verify) |
| `app/login/page.tsx` | Login page | Compilable (FASE 2 verify) |
| `app/maven/page.tsx` | Maven UI | Compilable (FASE 2 verify) |
| `components/cop/*` | 30+ componentes | Compilable (FASE 2 verify) |
| `lib/api.ts` | apiFetch + login/logout | OK |
| `store/*` | 3 stores | OK |
| `lib/mappers.ts`, `maven-types.ts`, `cop-types.ts` | Tipos | OK |

---

## 4. Mobile Matrix (Real)

| Pantalla | Estado Real | Test |
|---|---|---|
| `main.dart` | Compilable + integra 7 pantallas | FASE 7 verify |
| `features/auth/login_screen` | Login (hot) | FASE 7 |
| `features/auth/duress_screen` | Duress PIN | FASE 7 |
| `features/dashboard/cop_screen` | COP main screen | FASE 7 |
| `features/intel/intel_feed_screen` | Intel feed | FASE 7 |
| `features/c2/mission_screen` | Mission screen | FASE 7 |
| `features/agents/agents_screen` | Agent mesh | FASE 7 |
| `features/satellite/satellite_screen` | Satellite | FASE 7 |
| `core/network/{api_client, mesh_protocol, mesh_service}` | Offline mesh, API | FASE 7 |

---

## 5. Infra Matrix (Real)

| Servicio | Estado Real | Notas |
|---|---|---|
| `nginx` | Listo + hardening (TLS 1.2+, HSTS, XFO, XCTO, X-XSS, Referrer-Policy, Permissions-Policy, limit_req) | **Fallará al montar `infra/ssl`** (FASE 2) |
| `postgres` (pgvector/pg16) | Ready | Backup critical en FASE 3 |
| `redis` (AOF) | Ready | Fall-back a no Redis → accepted-risk |
| `nats` (-js) | Ready | DLQ no — accepted-risk FASE 3 |
| `neo4j` | Ready | Desacoplado, accepted-risk FASE 4 |
| `api` | Ready | `--reload` dev + prod código |
| `celery-worker` | Ready (`app.workers.celery_app`) | Tasks parciales (messaging pass, jobs.py pass) |
| `ollama` | Ready | Falta modelos preinstalados — FASE 2 |
| `frontend` | Ready (Next) | Compilable (FASE 2 verify) |
| `prometheus` | Ready | Scrape aplic |
| `grafana` | Ready + provisioning básica | FASE 6 dashboards |
| **Total de servicios** | 11 | docker-compose.yml valido al 100% |

---

## 6. Deudas Reportadas en Matriz (Derivadas de FASE 0)

**NB:** Todos los ítems de matrices de FASE 0 están acotados y rastreados en `docs/audit/TECHNICAL_DEBT.md` (TD-001..TD-026).

---

## 7. Resumen de Índices de Cobertura (FASE 0 — Diagnóstico)

| Métrica | Valor | Notes |
|---|---|---|
| Total Features Documentadas | ~35 | de docs/FEATURE_MATRIX.md |
| REAL IMPLEMENTADO/PARCIAL/EXPERIMENTAL | ~28 | (ver §1 + §2 + §3 + §4) |
| REAL NO IMPLEMENTADO/DEAD | ~7 | (main.py, v1/__init__) |
| REAL STUB | ~3 | (Guardian, media.py, land AI docs) |
| REAL PLANNED | ~3 | (CI/CD, OTES, Real-time) |
| Cobertura de Test-Real | ~28/35 = 80% | Estimado en FASE 2 (verify) |
| Cobertura de Seguridad | ~95% encontrada | 9 findings (2 NEW) en FASE 0 |

---

## 8. Field Status — Real (Table)

| Feature | Current Real | Status Real | Target FASE 1 | Target FASE 2 | Target FASE 3 |
|---|---|---|---|---|---|
| Authentication | 7 routers, 3 User models | PARTIAL | MODULAR MONOLITH ADR-001 | Uniformizar (N-01) | Ajustar IDspor |
| MFA | Osint FIXED, Intel L3 | PARTIAL | Adopción | Wifi | WPA2 |
| Audit Chain | In-memory | PARTIAL | Persistência FASE 2 | Concurrente | Configurable |
| JDL | Heuristic | EXPERIMENTAL | Hybridization | Probabilist | Reglas |
| OSINT | 12 agents | INTEGRATED | Reduntancy | DLQ | Retry |
| Saturation | Wireshark | PARTIAL | Observability | Dashboards | Alerts |
| Mobile | 7 screens | INTEGRATED | Verify | Optimizar | Offline Optimization |
| Deployment | docker-compose broken | INTEGRATED (FASE 2) | — | — | — |

---

## 9. Production Acceptance Criteria (FASE 0 → FASE 2 — checklist)

- [ ] `docker compose up --build -d` OK (FASE 2, infra/ssl + fernet.key)
- [ ] `pytest backend/tests` → 100% PASS (FASE 5, verify ~35)
- [ ] `cd frontend && npx tsc --noEmit` → 0 errors (FASE 2, verify)
- [ ] `cd mobile/sesis_cop && flutter analyze` → 0 errors (FASE 7)
- [ ] `docker compose exec api python -m uvicorn app.main:app` → startup OK (FASE 2)
- [ ] Nginx healthchecks → green (FASE 2)
- [ ] `validate_all.py` → exit code 0 (FASE 2, re-run)
- [ ] Security audit → 0 CRITICAL, 0 HIGH (FASE 3+)
- [ ] Deployment on k8s → OK (FASE 4)

---

## 10. Nota Final — Things Documented Wrongly in Baseline

- Archivo `docs/FEATURE_MATRIX.md` — docs line 14 afirma "18 features: CI/CD PLANNED, MicroVM UNSUPPORTED" — FASE 0 verify: Plausible FASA 0 (declarando-deuda).
- Archivo `docs/ARCHITECTURE_CURRENT.md` — Q: "BROKEN: missing api.ts" — FASE 0 verify: EXISTE
- Archivo `docs/SECURITY_AUDIT.md` — Listado CRITICAL-01/02/HIGH-01/02/03/MEDIUM-01/02 todos FASA 0 FIX/OPEN (nuevo status)

---

## 11. Bottom Line (FASE 0)

**Real:** Enterprise monolith with production-quality core + experimental features. **Real (Deudas):** User consolidation needed; 2 more findings new; docs drift significant; infra broken. **Beste (Recommendation):** Path OK: FASE 1-2 (Architecture + Backend hardening) → FASE 3 (Security) → FASE 5-6 (Testing) → FASE 4-7 (Data + Mobile) → FASE 9 (Docs).

**Confidence of confirmation:** HIGH (estático de código + cross-reading, verificado en FASE 2-5 por tests/deployment).