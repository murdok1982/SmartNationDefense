# DEPLOYMENT_ARCHITECTURE.md — Arquitectura de Despliegue (FASE 1)

**Doc ID:** ARCH-DEP-001 | **Estado:** FASE 1 — TARGET
**Fase AS-IS:** FASE 0 — docker-compose.yml valido; validcible (FASE 2: infra/ssl + fernet.key)

---

## 1. Despliegue Real (AS-IS)

```mermaid
flowchart TD
    LB[Nginx LB — pending FASE 2: TCP haproxy + healthz estático] --> API[FastAPI + Uvicorn]
    API --> PG[PostgreSQL 16 — pgvector + PostGIS]
    API --> RD[Redis — AOF]
    API --> NT[NATS JetStream]
    API --> NEO[Neo4j 5]
    API --> LLM[Ollama]
    API --> WF[Frontend (docker Next.js)]
    API --> MON[Prometheus + Grafana]
    CFG[Infra: docker-compose.yml] --> API
    CFG --> INFB[Vars: SECRET_KEY, MFA_ENCRYPTION_KEY, ADMIN_INITIAL_PASSWORD]
```

**Validibilidad AS-IS:**
- `docker compose config` → OK al 100%
- FALTA: `infra/ssl/` (Nginx mounts ./infra/ssl — TD-007)
- FALTA: `fernet.key` (api+celery mounts — TD-007)
- FALTA: `infra/docker-compose.demo.yml` (docs referencia — master prompt — FASE 0: gestionado FASE 2; no blocker)

---

## 2. Despliegue TARGET (FASE 1-2)

```mermaid
flowchart TD
    OP[Dev: make dev → uvicorn app.main:app] --> CONTAINERS[make up]
    CONTAINERS --> API[FastAPI + Uvicorn + Uvicorn<-->Redis>
    API --> PG[PostgreSQL 16 + pgvector + PostGIS]
    API --> RD[Redis — AOF]
    API --> NT[NATS JetStream]
    API --> NEO[Neo4j 5]
    API --> LLM[Ollama]
    API --> WF[Frontend (docker Next.js)]
    API --> MON[Prometheus + Grafana]
    LB[nginx] --> API
    LB --> WF
    ENV[Env: SECRET_KEY, MFA_ENCRYPTION_KEY, ADMIN_INITIAL_PASSWORD]
```

**FASE 2 actions:**
1. Create `infra/ssl/` with self-signed dev certs (`.gitignore`-d): `nginx.conf` + `server.crt` + `server.key`
2. Create `fernet.key`: `python scripts/generate_keys.py --name fernet --output fernet.key`
3. Document requirements: env vars mínimos, JWT keys, NATS urls
4. `docker compose up -d` verification (FASE 2 checklist)

---

## 3. Stack de Despliegue (Tabla)

| Servicio | Imagen/Comando | Port | Volumen | Notas |
|---|---|---|---|---|
| `postgres` | pgvector/pgvector:pg16 | 127.0.0.1:5432 | pgdata | Backup FASE 3 (TD-002 backup reg/cron) |
| `redis` | redis:7-alpine | 127.0.0.1:6379 | redisdata | AOF |
| `nats` | nats:2-alpine -js | 127.0.0.1:4222 | — | DLQ FASE 3 |
| `neo4j` | neo4j:5-community | 127.0.0.1:7474/7687 | neo4jdata | Desacoplado FASE 2 |
| `api` | backend (Dockerfile + uvicorn) | 127.0.0.1:8000 | backend:/app, fernet.key | Falta infra/ssl FASE 2 |
| `nginx` | nginx:alpine | 80, 443 | infra/ssl, infra/nginx.conf | FASE 2 fix |
| `celery-worker` | celery -A app.workers.celery_app | — | backend:/app | Worker pool (1 worker default) |
| `ollama` | ollama/ollama:latest | 127.0.0.1:11434 | ollamadata | Init-Time: (FASE 2) pull models |
| `frontend` | Next.js (docker) | 127.0.0.1:3000 | frontend:/app | FASE 2 build |
| `prometheus` | prom/prometheus:latest | 127.0.0.1:9090 | promdata | Scrape api:8000 |
| `grafana` | grafana/grafana:latest | 127.0.0.1:3001 | grafanadata | Provisioning FASE 6 |

---

## 4. Environements (FASE 0-5: planning + AS-IS)

| Entorno | Valores críticos | Validación (FASE 2) |
|---|---|---|
| **development** | SECRET_KEY lenient, MFA_ENCRYPTION_KEY opcional, ADMIN_INITIAL_PASSWORD=admin123 (HIGH-02) | docker compose up (FASE 2) |
| **staging** | Secrets, MFA_ENCRYPTION_KEY real (64 hex) | 2-step validate (FASE 3-5) |
| **production** | Validación real (`validate_production_hardening`): SECRET_KEY ≠ defaults, NEO4J_PASSWORD, ADMIN_INITIAL_PASSWORD, MFA_ENCRYPTION_KEY, GRAFANA_ADMIN_PASSWORD — todo requerido, DEMO_MODE ≠ true | Startup validation (FASE 2) |

**Validador actual:** `Settings.validate_production_hardening` en `app/core/config.py:80-110` (validator real en FASE 0).

---

## 5. Escalabilidad (Nivel Maturity, de A)

| Nivel | Estado | Notas |
|---|---|---|
| **Level 0 — Manual Scaling** | ✅ | `docker compose up --scale api=2` (round-robin DNS nativo) — FASE 2 |
| **Level 1 — Container Health Checks** | ✅ | healthchecks en api + frontend |
| **Level 2 — Vertical Scaling (Postgres)** | ✅ | `docker update` + restart pg (FASE 3) |
| **Level 3 — Horizontal Redis (Read Replica)** | ✅ Planned (FASE 5) | `REDIS_SLAVES` env |
| **Level 4 — NATS Clustering** | PLANNED (FASE 3) | nats:cluster B+D configurations |
| **Level 5 — K8s + Helm + GitOps** | PLANNED (FASE 4) | helm-chart + values |

---

## 6. Despliegue y Seguridad (Security Hardening — FASE 2)

| ID | Título | Status FASE 0 | FASE 2 | Nota |
|---|---|---|---|---|
| D-01 | LocalDB /loopback privileged | ✅ Fixed | — | Docker (falta infra/ssl) — FASE 2 fix |
| D-02 | Network boundaries + cross-zone traffic | ✅ | — | Nginx/Network separation FASE 2 |
| D-03 | Non-root + secrets not exposed | ✅ | — | FASE 2: volumes mínimos |
| D-04 | SSRF + TLS | ✅ | — | FASE 3 |
| D-05 | XSS Hardening CSP + SRI | ✅ | — | X-XSS deprecado, FASE 2 |

---

## 7. Devops — quality Cycle

**Pipeline:** `validate_all.py` → `pytest` → `npm run build` → `flutter analyze` → `alembic heads` → `docker compose up` → OWASP scans → E2E scripts

---

## 8. Links

- [`docs/architecture/SYSTEM_OVERVIEW.md`](SYSTEM_OVERVIEW.md) — visión general
- [`docs/architecture/ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md) — ADR 1-13
- [`docs/architecture/DATA_FLOW.md`](DATA_FLOW.md) — Data Flow
- [`docs/architecture/SECURITY_ARCHITECTURE.md`](SECURITY_ARCHITECTURE.md) — Security Arch
- [`docs/audit/REPOSITORY_AUDIT.md`](../audit/REPOSITORY_AUDIT.md) — FASE 0 audit
- [`docs/audit/SECURITY_AUDIT.md`](../audit/SECURITY_AUDIT.md) — FASE 0 audit findings
- [`.factory/TASKS.md`](../.factory/TASKS.md) — Backlog atómico
- [`Makefile`](../../Makefile) — DevOps commands
- [`docker-compose.yml`](../../docker-compose.yml) — Docker Compose (REAL)
- [`.env.example`](../../.env.example) — Env Configuration (REAL)

---

## 9. Resumen

- Despliegue: Docker Compose real (11 services), FASE 2 fix (infra/ssl + fernet.key)
- Despliegue target: Docker Compose + Docker Hub (FASE 4) → K8s (FASE 5)
- Security hardening real: HSTS, XFO, XCTO, XSS, Referrer-Policy, Permissions-Policy, CSP — FASE 2 (nginx-side)
- Backup: FASE 2 (DB backup scripts) — FASE 3 (R2, Cloud, HA)
- Hardening maturity (Levels 0-5): FASE 2 (Level 0-1) → FASE 4 (Level 3-5)