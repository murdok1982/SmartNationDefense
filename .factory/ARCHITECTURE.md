# SYSTEM ARCHITECTURE & DESIGN SYSTEM BLUEPRINT (FACTORY)

- **Project Name:** SmartNationDefense / SESIS-FEDERATION
- **Architecture Status:** `LOCKED`
- **Primary Runtime & Stack:** FastAPI 0.115.6 + SQLAlchemy 2.0.36 + Redis + NATS + Neo4j + Ollama; Next.js 14.2.35 + React 18.2 + Tailwind; Flutter (5+ screens, offline mesh); Nginx + Docker Compose.
- **Last Updated By:** `@architect` (FASE 0-1)

---

## 1. TECH STACK & PINNED DEPENDENCIES

| Layer | Technology / Package | Version | Purpose & Architectural Justification |
| :--- | :--- | :--- | :--- |
| **Backend / API** | FastAPI 0.115.6, Uvicorn 0.34.0 | 0.115.6 | Core server + REST routers (api/v1, v2, v3, tactical, osint, sat) |
| **ORM/DB** | SQLAlchemy 2.0.36, Alembic 1.14.0 | 2.0.36 | DB ORM + migrations |
| **Persistence** | PostgreSQL 16 (pgvector+PostGIS), Redis 7 (AOF), Neo4j 5 | — | Persist, Cache, Graph (Partial) |
| **Messaging** | NATS JetStream, Celery 5.4.0 (workers) | 2.9.0 | Event bus + background workers |
| **Auth & Crypto** | HS256 (jose), bcrypt (passlib), AESGCM (cryptography 44.0.0) | — | JWT + passwords + MFA AES-256-GCM at rest |
| **CV** | OpenCV 4.10.0.84, YOLOv8 8.3.0, torch 2.5.1 | — | YOLO inference + OpenCV |
| **OSINT** | httpx, BeautifulSoup4, lxml, trafilatura | — | Scrapers + tools suite |
| **Frontend / UI** | Next.js 14.2.35, React 18.2, Tailwind 3.4, Zustand 4.4, Leaflet, Recharts | 14.2.35 | Web COP dashboard |
| **Móvil** | Flutter (Flutter-version 3.x, e.g., 3.24+), Flutter 3.24+ | — | Tactical COP offline-first |
| **Infra** | Nginx (alpine), Docker Compose, Prometheus, Grafana | — | Deployment |
| **Testing & QA** | pytest 8.3.4, pytest-asyncio 0.25.0, backend/tests/ | 8.3.4 | Unit/integration/security tests |

---

## 2. DIRECTORY & MODULE TOPOLOGY

```text
SmartNationDefense/
├── backend/
│   ├── app/
│   │   ├── api/                # Routers (v1 legacy/modern, v2, v3, tactical, osint, sat, agents)
│   │   ├── core/               # security (JWT), audit (AuditChain), crypto (AESGCM), mfa
│   │   ├── db/                 # models (persistence, intel, osint, messaging, opord, aar), session, init_db
│   │   ├── services/           # intel, osint, sat, tactical, mapping, prediction, voice, logistics, security (UEE)
│   │   ├── agents/             # osint agents, intel agents
│   │   ├── workers/            # celery_app
│   │   └── main.py             # FastAPI app entrypoint
│   ├── migrations/             # Archivado (legacy, alembic/ Versions is real)
│   ├── alembic/versions/       # 001_sesis_initial, 002_audit_chain (REAL)
│   └── tests/                  # conftest + 9 test suites
├── frontend/                   # Next.js 14 — app/{page, login, maven, globals.css}, components/cop/, store/
├── mobile/sesis_cop/           # Flutter — 7 screens, core/network (api_client, mesh_protocol, mesh_service), dark theme
├── ml/                         # vision.py, anomalies.py, correlation.py, correlation_engine.py, briefing.py, rules/
├── infra/                      # nginx.conf, prometheus.yml, grafana/provisioning/, ssl/ (FASE 2), certs (FASE 2)
├── compliance/                 # ENS_ALTA_matrix.md, STANAG_4774_4778.md
├── docs/                       # audit/*, architecture/*, API.md, etc.
├── .factory/                   # SPEC, ARCHITECTURE, TASKS, SECURITY_AUDIT (factory SDD)
├── scripts/                    # validate_all.py, seed_data.py, generate_keys.py, demo.sh/bat
├── docker-compose.yml          # 11 services (API+Frontend+Celery+NGINX+Monitoring)
└── reports/                    # validation.json
```

---

## 3. DATA LAYER & SCHEMA CONTRACTS

### Entity: `users` — Multi-Model Architecture (ADR-003 — FASE 2 Completion)

**AS-IS (FASE 0 — 3 collisiones REAL):**
| Tabla | Dominio | Columnas chave |
|---|---|---|
| `users` (persistence) | Auth principal | username, email, hashed_password, role, classification_level, is_active, last_login, last_ip |
| `users` (intel) | Inteligencia | email, hashed_password, full_name, clearance, tenant_id, mfa_enabled |
| `users` (osint) | OSINT | id(string), username, email, hashed_password, scopes, classification, mfa_enabled |

**TARGET (ADR-003):** Unified User (`persistence.User`) + `IntelUserSchema` + `OsintUserSchema` (como schemas, mixins), ADR-003. FASE 2: consolidación (AC-08).

### Entity: `audit_log`
| Columna | Tipo | Restricción | Notas |
|---|---|---|---|
| id | INTEGER AUTOINCREMENT | PK | Integer + DB recuperable (row_hash+prev_hash) |
| ts | TIMESTAMPTZ | DEFAULT NOW() | Audit timestamp |
| actor | VARCHAR(256) | NOT NULL | User ID |
| action | VARCHAR(256) | NOT NULL | Event type |
| resource_type | VARCHAR(64) | NOT NULL | User resource type |
| resource_id | VARCHAR(64) | NOT NULL | Resource identifier |
| context | JSON | DEFAULT {} | Detail metadata |
| prev_hash | VARCHAR(64) | NOT NULL | Previous chain hash |
| row_hash | VARCHAR(64) | NOT NULL | SHA-256 chain hash |

### Entity: `events` — Core tactical data (persistence.py:79)
| Columna | Tipo | Notas |
|---|---|---|
| event_id | VARCHAR | PK |
| event_type | VARCHAR | Classifies events |
| asset_id | VARCHAR FK | Link to assets |
| ts | TIMESTAMPTZ | Timestamp |
| lat/lon | Float | GPS |
| classification_level | VARCHAR | Clearance |
| confidence_score | Float | 0-1 |
| payload | JSON | Event data |
| signature | JSON | Cryptographic signature (UEE — JWS Ed25519 verify fail-closed in non-dev) |

### Entity: `assets` (persistence.py:66) — Sensors + Assets (satélite, radares, drones)
| Columna | Tipo | Notas |
|---|---|---|
| id | VARCHAR | PK |
| kind | VARCHAR | type of asset |
| current_status | VARCHAR | ACTIVE/INACTIVE |
| last_heartbeat | TIMESTAMPTZ | Heartbeat tracking |
| lat/lon | Float | GPS |
| classification_level | VARCHAR | Clearance |
| metadata_json | JSON | metadata |

### Entity: `alembic_versions`
- Real schema source (FASE 0): `alembic/env.py` + `versions/001_sesis_initial.py` + `versions/002_audit_chain.py`.
- AS-IS: `migrations/*.legacy` desactualizados (TD-012).

---

## 4. API & SERVER CONTRACTS

| Method | Endpoint | Auth / Role | Success Response | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| POST | `/api/v1/auth/login` | Public (JWT HS256) | `200 { access_token, refresh_token }` | `401` |
| POST | `/api/v1/auth/register` | Public (operator, inactive) | `201 UserResponse` | `409` |
| POST | `/api/v1/auth/refresh` | Public | `200 TokenResponse` | `401` |
| POST | `/api/v1/auth/logout` | Auth | `200` | `401` |
| GET | `/api/v1/auth/me` | Auth | `200 UserResponse` | `401` |
| POST | `/api/v1/osint/auth/login` | Public (JWT + MFA AES-256-GCM challenge — FIXED) | `200 { mfa_required: true, mfa_ticket }` | `401, 429` |
| POST | `/api/v1/osint/auth/mfa/verify` | Public (MFA ticket) | `200 { access_token, refresh_token }` | `401` |
| POST | `/api/v1/osint/auth/mfa/enable` | Auth | `204` | `400, 401` |
| POST | `/api/v1/osint/auth/mfa/setup` | Auth | `200 { secret, otpauth_uri }` | `401` |
| POST | `/api/v1/intel/auth/login` | Public (L3 TOTP challenge) | `200 { access_token, refresh_token }` | `401, 429` |
| GET | `/api/v1/c2/alerts` | clearance enforcement + GET | `200 { alerts[] }` | `401, 403` |
| GET | `/api/v2/c2/...` | clearance enforcement (c2, space, border, cyber, logistics, ew, space) | `200` | `401, 403` |
| GET | `/api/v1/satellite/*` | clearance enforcement (SECRET) | `200` | `401, 403` |
| GET | `/api/v1/osint/cases` | clearance enforcement (RESTRICTED) | `200 { cases[] }` | `401, 403` |
| GET | `/api/v1/osint/entities` | clearance enforcement | `200 { entities[] }` | `401, 403` |
| GET | `/api/v1/osint/web_fetch` | clearance enforcement + SSRF-protected | `200 { url, final_url, status_code, ... }` | `400, 401, 403` |
| GET | `/api/v1/osint/reports` | clearance enforcement | `200 { reports[] }` | `401, 403` |
| GET | `/api/v1/osint/graph` | clearance enforcement + Neo4j query | `200 { nodes[], edges[] }` | `401, 403` |
| GET | `/api/v1/osint/external` | clearance enforcement | `200 { results[] }` | `400, 401, 403` |
| POST | `/api/v1/osint/dns` | clearance enforcement | `200 { dns[] }` | `400, 401, 403` |
| GET | `/api/v1/agents/status` | Public JWT (get_current_user) | `200 { status: operational }` | `401` |
| POST | `/api/v1/voice/command` | Auth (VOICE) | `200 { response }` | `401, 400` |
| GET | `/api/v1/planning/opord` | Auth | `200 { opord[] }` | `401` |
| GET | `/api/v1/prediction/threats` | Auth | `200 { threats[] }` | `401` |
| GET | `/api/v1/voice/commands` | Auth | `200 { commands[] }` | `401` |
| GET | `/api/v3/maven/inventory` | Auth | `200 { inventory }` | `401` |
| GET | `/api/v1/health` | Public | `200 { status: healthy }` | — |

---

## 5. UI DESIGN SYSTEM (`@ui-artisan` CONTRACT)

- **Aesthetic Personality:** Military tactical (oscuro, high density, diagonal, white-on-black), practical, tasteful.
- **Color Tokens (globals.css, FASE 2 update):**
  - `--bg-canvas: #0b1220` | `--bg-surface: #111827` | `--bg-elevated: #1f2937`
  - `--border-subtle: #1e293b` | `--border-strong: #334155`
  - `--text-primary: #f8fafc` | `--text-secondary: #94a3b8` | `--text-muted: #64748b`
  - `--accent-primary: #10b981` | `--accent-foreground: #059669`
  - `--status-success: #10b981` | `--status-warning: #f59e0b` | `--status-danger: #ef4444`
- **Typography & Rhythm:** Inter (sans), JetBrains Mono (mono). Spaces in ms: gap-2, gap-4, p-6, p-8 (8px scale). Radii: --radius-sm: 6px, --radius-md: 10px, --radius-lg: 14px.
- **Mandatory Component Standards:**
  - All async tables/lists: skeleton + empty + error states (TD-019).
  - Forms: inline validation + aria-busy on submit.
  - Responsive: 375px mobile, 768px tablet, 1440px desktop.
- **Mobile:** Flutter tactical-dark theme, Duress mode, offline-first (FASE 7).

---

## 6. SECURITY & INFRASTRUCTURE HARDENING

- **Auth/MFA:** JWT HS256, MFA (osint AES-256-GCM at rest + challenge isolation + single-use Redis, FIXED FASE 0; intel L3 TOTP challenge). AuthMiddleware fail-open → enforcement via require_clearance in v2 + v1 (N-01).
- **SSRF:** `web_tools.py` denylist amplio + TOCTOU (HIGH-03 — FASE 3 IP pinning).
- **Audit Chain:** SHA-256 chain + asyncio.Lock, in-memory (TD-002 — FASE 2/3 persistence).
- **HTTP Security Headers (Nginx, infra/nginx.conf):** HSTS, X-Frame-Options, X-Content-Type-Options, X-XSS (deprecated), Referrer-Policy, Permissions-Policy, Content-Security-Policy, Rate Limit (30r/s).
- **Network:** Docker networks (backend), DDoS limits (TD-019), FASE 2 security orchestration (ADR-008).
- **Error Handling:** Centralized (`app/api/*.py` — 403 on denial, 401+refresh, 404 with existence-hiding), no stack traces to clients, gzipped responses.

---

## 7. ARCHITECTURAL DECISION RECORDS (ADR) & CIRCUIT BREAKER LOG

> `@architect` registra aquí cualquier cambio estructural motivado por un bloqueo de 3 fallos consecutivos en `TASKS.md`.

- **ADR-001:** Modular Monolith (vs Microservices) — User preference + 3 collisiones. (FASE 0)
- **ADR-002:** Layers: Presentation/API/Application/Domain. (FASE 1)
- **ADR-003:** User consolidation: Unified User + IntelUserSchema + OsintUserSchema. (FASE 1, FASE 2)
- **ADR-004:** Auth consolidation: Unified Auth Router. (FASE 1)
- **ADR-005:** SSRF IP pinning (HIGH-03). (FASE 1, FASE 3)
- **ADR-006:** Clearance enforcement v1 (N-01). (FASE 1, FASE 2)
- **ADR-007:** Alembic vs legacy migrations — Alembic real. (FASE 0, FASE 2 legacy archive)
- **ADR-008:** Infra hardening (infra/ssl + fernet.key). (FASE 1, FASE 2)
- **ADR-009:** NATS DLQ + workers. (FASE 1, FASE 3)
- **ADR-010:** Clearance hierarchy Open (v1 leak reduction). (FASE 1, FASE 5)
- **ADR-011:** MVP hardening (FASE 2). (FASE 1)
- **ADR-012:** Security hardening + SEC-FIX-XXX (FASE 3). (FASE 1)
- **ADR-013:** Docs regeneration (FASE 9). (FASE 1)

**Registro de circuit breaker:** N/A (no 3/3 fallos reales registrados — FASE 0-2). Verificar en FASE 3+ si se produce.

---

## 8. LINKS

- [`docs/audit/REPOSITORY_AUDIT.md`](../docs/audit/REPOSITORY_AUDIT.md) — FASE 0: Inventario real
- [`docs/audit/SECURITY_AUDIT.md`](../docs/audit/SECURITY_AUDIT.md) — FASE 0: Hallazgos reales
- [`docs/audit/FEATURE_MATRIX.md`](../docs/audit/FEATURE_MATRIX.md) — FASE 0: Matriz real
- [`docs/architecture/SYSTEM_OVERVIEW.md`](../docs/architecture/SYSTEM_OVERVIEW.md) — FASE 1: Overview
- [`docs/architecture/ARCHITECTURE_DECISIONS.md`](../docs/architecture/ARCHITECTURE_DECISIONS.md) — FASE 1: ADR-001..013
- [`docs/architecture/DATA_FLOW.md`](../docs/architecture/DATA_FLOW.md) — FASE 1: Data Flow
- [`docs/architecture/SECURITY_ARCHITECTURE.md`](../docs/architecture/SECURITY_ARCHITECTURE.md) — FASE 1: Security Arch
- [`docs/architecture/DEPLOYMENT_ARCHITECTURE.md`](../docs/architecture/DEPLOYMENT_ARCHITECTURE.md) — FASE 1: Deployment Arch
- [`.factory/TASKS.md`](./TASKS.md) — Backlog atómico (FASE 2-9)
- [`docs/TRANSFORMATION_PROGRESS.md`](../docs/TRANSFORMATION_PROGRESS.md) — Estado de fases
- [`docs/TECHNICAL_DECISIONS.md`](../docs/TECHNICAL_DECISIONS.md) — Registro de decisiones
