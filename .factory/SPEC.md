# PROJECT SPECIFICATION (SINGLE SOURCE OF TRUTH)

- **Project Name:** SmartNationDefense / SESIS-FEDERATION
- **Status:** `IN_PROGRESS`
- **Target Stack:** FastAPI 0.115.6 + SQLAlchemy 2.0.36 + Alembic + PostgreSQL 16 (pgvector+PostGIS) + Redis 7 + NATS 2 + Neo4j 5 + Ollama + Celery; Next.js 14 (Web COP); Flutter (Tactical COP); Nginx + Docker Compose (11 services).
- **Last Updated By:** `@architect`

---

## 1. SCOPE & BOUNDARIES

### 1.1 In-Scope (Entregables Obligatorios)
- **FASE 0 (Audit):** Inventario real (archivos, stacks, APIs, módulos, deps), hallazgos de seguridad verificados en código, matriz de funcionalidades, deuda técnica, evaluación de arquitectura. Entregables: `docs/audit/*`.
- **FASE 1 (Arquitectura Target):** Modular Monolith, system overview, ADR-001..013 (alternativas + recomendaciones), data flow, security architecture, deployment architecture. Entregables: `docs/architecture/*`.
- **FASE 2 (Backend Hardening) — TD-003, TD-006, TD-008, TD-009, TD-010, TD-012, TD-013, TD-014, N-01, N-02, N-04, N-06, N-07, N-08, N-09:** Consolidación User unified (ADR-003), clearance enforcement v1 (N-01 + SEC-TEST-CLEARANCE-01..08), EncryptedField fail-closed (TD-006), rate-limit path-fix (TD-009, N-06, TD-019), circuit breaker rate-limit (TD-010), settings defaults (TD-008), Alembic legacy archivado (TD-012), Guardian quarantine (TD-013), infra/ssl + fernet.key (N-07, TD-007), X-XSS fix (N-09), dead route removal (N-08).
- **FASE 3 (Security — SEC-FIX-XXX, accepted-risk mitigation):** HIGH-02 remediados (admin123 defaults, verificación startup, secrets rotos en staging/dev), HIGH-03 SSRF IP pinning (TASK — FASE 3), MEDIUM-01 audit chain persistence (TD-002 + FASE 2 fix confirmado), MEDIUM-02 crypto_quantum labels (FASE 3), NATS DLQ (TD-009 FASE 2, DLQ FASE 3), redteam re-run → 0 CRITICAL/HIGH.
- **FASE 5 (Testing):** SEC-TEST-AUDIT-01, SEC-TEST-BRUTE-01, SEC-TEST-CLEARANCE-01, SEC-TEST-MFA-01, SSRF hardened suite, re-run `pytest backend/tests` → verde.
- **FASE 6 (Observability):** Dashboards por módulo, alerts, TD-020.
- **FASE 7 (Mobile):** pubspec completion, `flutter analyze` → 0 errors.
- **FASE 9 (Docs regeneration):** `docs/{ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md}` a partir de realidad FASE 0/1/2.

### 1.2 Out-of-Scope (Exclusiones Explícitas)
- No nuevas features.
- No refactorización de JDL L0-4 heurístico (FASE 2 experimental → probabilístico en FASE 5+ FASE 4).
- No elminación de las tablas `users` reales (compatibilidad — FASE 2 y 4).

---

## 2. USER ROLES & ACCESS MATRIX

| Role | Description | Auth Required | Allowed Resources / Actions |
| :--- | :--- | :--- | :--- |
| `guest` | Usuario no autenticado | No | `/`, `/health`, `/docs`, `/openapi.json`, auth login/register/refresh (publico) |
| `admin_persistence` | Admin de C2 | Sí (JWT access TOP_SECRET) | Todos routers v2 (c2, border, cyber, ew, logistics, space), API v3 (maven, coa), messaging, logistics v1 |
| `operator_persistence` | Operador tactico | Sí (JWT access RESTRICTED) | Routers v1 legacy, assets, intel, sensors, timeline |
| `analyst_intel` | Inteligencia (Global-Intel, Intel, Intel Agents) | Sí (JWT + TOTP MFA challenge api/intel/auth) | `/api/v1/intel/*`, `/api/v1/c2/*`, módulos de inteligencia |
| `analyst_osint` | OSINT (Atalaya, osint, satellite, tactical v2) | Sí (JWT + MFA AES-256-GCM + single-use Redis) | `/api/v1/osint/*`, `/api/v1/satellite/*`, `/api/v2/c2/*` |
| `tactical` | Voice/plataforma táctica | Sí (JWT access) | Voice, tactical OPORD, etc. |
| `demo_analyst` | Usuario Demo (MFA on intel) | Sí (JWT + TOTP MFA) | Modo DEMO accessible por clearance |

---

## 3. FUNCTIONAL REQUIREMENTS & ACCEPTANCE CRITERIA

### Feature F-01 — FASE 0 + FASE 1 (Complete)
- **REQ-01:** FASE 0: `docs/audit/*` (REPOSITORY_AUDIT.md, TECHNICAL_DEBT.md, SECURITY_AUDIT.md, FEATURE_MATRIX.md, ARCHITECTURE_ASSESSMENT.md) instanciados desde plantilla, con inventario real.
  - [ ] **AC-01:** Documentar real inventory real (todos los stacks, APIs, módulos listados con paths). *(Verified FASE 0)*
  - [ ] **AC-02:** Identificar hallazgos reales CRITICAL/HIGH/MEDIUM/LOW verificados en código. *(Verified FASE 0)*
  - [ ] **AC-03:** Matriz de funcionalidades documentada como IMPLEMENTADO/PARCIAL/EXPERIMENTAL/NO IMPLEMENTADO/STUB/PLANNED/UNSUPPORTED real. *(Verified FASE 0)*
- **REQ-02:** FASE 1: `docs/architecture/*` (SYSTEM_OVERVIEW.md, ARCHITECTURE_DECISIONS.md, DATA_FLOW.md, SECURITY_ARCHITECTURE.md, DEPLOYMENT_ARCHITECTURE.md) con decisiones ADR-001..013.
  - [ ] **AC-04:** SYSTEM_OVERVIEW.md documenta ADR-001 (Modular Monolith). *(Verified FASE 1)*
  - [ ] **AC-05:** ARCHITECTURE_DECISIONS.md documenta ADR-001..013 con alternativas + recomendaciones. *(Verified FASE 1)*
  - [ ] **AC-06:** DATA_FLOW.md contiene Mermaid diagrams reales. *(Verified FASE 1)*
  - [ ] **AC-07:** SECURITY_ARCHITECTURE.md y DEPLOYMENT_ARCHITECTURE.md documentan Stack, Environments, Security Hardening FASE 2. *(Verified FASE 1)*

### Feature F-02 — FASE 2 (Backend Hardening, PENDING — see TASKS.md)
- **REQ-03:** Consolidación de User (TD-001 + ADR-003): Unified User model + IntelUserSchema + OsintUserSchema (como mixins/interfaces).
  - [ ] **AC-08:** User unificado exportado desde `app/db/models/persistence.py` + `app/db/models/__init__.py` no colisiona. *(Verified FASE 2)*
  - [ ] **AC-09:** Routers v1 clearance-enforced (N-01 + SEC-TEST-CLEARANCE-01..08 passing). *(Verified FASE 2)*
  - [ ] **AC-10:** EncryptedField fail-closed (TD-006). *(Verified FASE 2)*
  - [ ] **AC-11:** Rate-limit path-blindness fixed (TD-009, N-06). *(Verified FASE 2)*
  - [ ] **AC-12:** X-XSS-Protection fix (TD-019 + N-09). *(Verified FASE 2)*
  - [ ] **AC-13:** Legacy `backend/migrations/*.legacy` archived (TD-012). *(Verified FASE 2)*
- **REQ-04:** FASE 2 infra hardening (N-07, TD-007, TD-020): infra/ssl + fernet.key + healthzestatic.
  - [ ] **AC-14:** infra/ssl/ configurado para nginx (dev certs self-signed, .gitignore-d). *(Verified FASE 2)*
  - [ ] **AC-15:** fernet.key generado + documentado. *(Verified FASE 2)*
  - [ ] **AC-16:** Healthcheck estático en nginx (TD-020). *(Verified FASE 2)*
  - [ ] **AC-17:** Guardian scripts quarantined (TD-013). *(Verified FASE 2)*

### Feature F-03 — FASE 3 (Security, PENDING — see TASKS.md)
- **REQ-05:** HIGH-02 remediación real: ADMIN_INITIAL_PASSWORD en develop/staging con advertencias (necesario FASE 3+); POSTGRES_PASSWORD rotado; validación de startup real.
  - [ ] **AC-18:** Despliegue en staging con credenciales personalizadas → validate_all.py exit 0. *(Verified FASE 3)*
- **REQ-06:** SSRF IP pinning (HIGH-03, TD-004, SEC-04, N-02).
  - [ ] **AC-19:** socket-level pinning en connect() → WAF URL. *(Verified FASE 3)*
- **REQ-07:** Audit chain persistence (MEDIUM-01, TD-002).
  - [ ] **AC-20:** `audit_chain.record()` persiste en DB en producción; `verify_chain()` pasa; tamper detection real. *(Verified FASE 3+FASE 5)*
- **REQ-08:** Quantum label fix (MEDIUM-02, TD-005).
  - [ ] **AC-21:** crypto_quantum.py labela AES-256-GCM honestamente (Fernet → aes-128-cbc-hmac). *(Verified FASE 3)*

### Feature F-04 — FASE 5 (Testing, PENDING — see TASKS.md)
- **REQ-09:** New security suites: SEC-TEST-AUDIT-01, SEC-TEST-BRUTE-01, SEC-TEST-CLEARANCE-01, SEC-TEST-MFA-01, SSRF hardened suite.
  - [ ] **AC-22:** pytest → todos passing, coverage security suites 80%+ (FASE 5). *(Verified FASE 5)*
- **REQ-10:** Full: validate_all.py exit 0. *(Verified FASE 5)*

### Feature F-05 — FASE 6 (Observability, PENDING — see TASKS.md)
- **REQ-11:** Grafana dashboards: C2, Auth, OSINT, Tactile, Maven, Security (TD-020).
  - [ ] **AC-23:** Dashboards provisioned + with metrics en FASE 6. *(Verified FASE 6)*
- **REQ-12:** Alertmanager config + alerts (TD-020).
  - [ ] **AC-24:** Alerts activos. *(Verified FASE 6)*

### Feature F-06 — FASE 7 (Mobile, PENDING — see TASKS.md)
- **REQ-13:** Mobile: pubspec completo + offline mesh hardened.
  - [ ] **AC-25:** `flutter analyze` → 0 errors, `flutter test` → pass (FASE 7). *(Verified FASE 7)*

### Feature F-07 — FASE 9 (Docs Regeneration, PENDING — see TASKS.md)
- **REQ-14:** Docs regenerate desde realidad FASE 0/1/2: ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md, SECURITY_AUDIT.md (base, FASE 2+).
  - [ ] **AC-26:** Todos docs regenerados + coherencia con realidad verificada FASE 9. *(Verified FASE 9)*

---

## 4. UI/UX & AESTHETIC CONTRACT (`@ui-artisan` Gate)

- **Visual Direction:** Military tactical (oscuro, high density, white-on-black diagonal), practical, tasteful.
- **Design Tokens (FASE 1/2):** `docs/architecture/SECURITY_ARCHITECTURE.md` (Colores) + `frontend/src/app/globals.css` + `.factory/ARCHITECTURE.md` — definidos reales.
- **Mandatory UI States:** [FASE 2 per app: skeleton, empty, error — TD-019]
- **Responsiveness & Accessibility:** [WCAG AA]

---

## 5. EDGE CASES & ERROR HANDLING MATRIX

| Scenario | Trigger | Expected System Behavior | HTTP Status |
| :--- | :--- | :--- | :--- |
| Payload malformado | JSON inválido | 400 + error schema estructurado | `400` |
| Token expirado/ausente | Protected route | 401 + retry con refresh | `401` |
| IDOR cross-resource | User A vs User B | 403, denial + log | `403` |
| Rate Limit excedido | Auth > N/min | 429 + Retry-After | `429` |
| DB down | PG offline | 503 + JSON body + log | `503` |
| SSRF blocked | Interna URL | 400 estructurado + WAF | `400` |
| Authentication rechazada | mfa_challenge as bearer | 401 "Invalid token type" | `401` |
| DB down | Bajada DB | Health degrade → unhealthy | `503` |
