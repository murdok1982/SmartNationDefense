# ARCHITECTURE_DECISIONS.md — Registro de Decisiones Arquitectónicas (FASE 1)

**Doc ID:** ARCH-DEC-001 | **Estado:** FASE 1 — DECISIONES (diseño de FASE 1, AS-IS confirmada FASE 0)
**Fecha:** 21-11-2026

> **Regla:** Decisiones reales/verificables (FASE 0 audit confirma), con alternativas comparadas. ADRs en `.factory/ARCHITECTURE.md` per GATE-001.

---

## ADR-001 — MODULAR MONOLITO vs MICROSERVICES (DECISION — CONFIRMADO FASE 0)

**Contexto:** FASE 0 audit mostró: 3 modelos `User` collisiones, 3 routers de auth fragmentados, doc requirementes "MicroVM sandboxing" falsas, claim "Microservicios" sin código backings.

**Decisión:** Modular monolith (sin microservicios).

**Alternativas:**

| Alternativa | Por qué rechazada | Status |
|---|---|---|
| **Microservicios** (3: backend, auth, intel) | 3 modelos User colisionan, 3 routers auth, migración compleja, nada más | NO |
| **Modular Monolith** (10 módulos: core, auth, sat, osint, intel, tactical, sat-map, móvil, ml, agency) | Documentada: user preference, 100% compatible con reality, minimal deuda | YES |

**Causas:** modular llamado + stacks distribuidos funcionales + Elasticsearch/NATS/Neo4j en stacks de C4ISR + init_db en un solo proceso. El backend actual es monolito nativo.

**No se decidió:** REST en modo microservicios (porque redeploy severity is low — código no lo justifica en FASE 0).

---

## ADR-002 — LAYERS ARQUITECTÓNICAS (DECISION)

**Contexto:** stacks entre capas — qué va en Presentation, API, Application, Domain.

**Decisión:** Layered Architecture con capas:
- **Presentation (API)**: FastAPI (backend) + Next.js (web) + Flutter (móvil)
- **API/Gateway**: FastAPI + nginx edge + middleware (AuthMiddleware, RateLimitMiddleware)
- **Application/Core**: security (JWT HS256, MFA challenge, refresh rotation), auth_middleware, rate_limit, audit (AuditChain), crypto (AESGCM), classification, pipeline
- **Services/Infrastructure**: osint/*, sat/*, intel/*, tactical/*, mapping/*, prediction, voice, logistics, aar, reports, fusion, terrain, security (UEE), policy
- **Domain/Persistence**: persistence.py, intel/*, osint/*, messaging.py, opord_enhanced.py, aar.py
- **Data/Event**: PostgreSQL (16 + pgvector + PostGIS), Redis (AOF), NATS (JetStream), Neo4j, Ollama

**Justificación:** Quick verification del stack, fácilado test, integración seamless con legacy backends.

---

## ADR-003 — CONSOLIDACIÓN DE USER (DECISION)

**Contexto:** TD-001: 3 modelos User con tabla `users` collisionada.

**Decisión:** Unified User model (`app/db/models/persistence.py`) + IntelUserSchema (`app/db/models/intel/user.py`) + OsintUserSchema (`app/db/models/osint/user.py`) — por tipo, que heredan de User (para permitir mixins intel/osint). TD-001 leyendo universidades (FASE 2-4).

**Alternativas:**
1. Namespaceo tables: `intel_users` + `osint_users` —quick fix FASE 2
2. Unified User single entity — vertical es agregado ámbar para inteligencia

**Recomendación:** Unified User single entity (según ad model actual el mejor).

---

## ADR-004 — AUTH CONSOLIDADO (DECISION)

**Contexto:** TD-001/TD-002/N-01 — 3 routers de auth fragmentados + enforcement regular de clearance en v1.

**Decisión:** `app/api/auth/*` — Fixed Implementation + Uniformizar `require_clearance` enforcement en routers v1.

**Alternativas:**

| Alternativa | Status | Notas |
|---|---|---|
| Consolidar en single router de autenticación | NO — si temporal, calculable alto de switches entre routers pares (legacy/osint/intel) | |
| Uniformizar todos en v1 | SI | clearances y endpoints) |

---

## ADR-005 — SSRF HARDENING (DECISION — PARTIAL)

**Contexto:** HIGH-03 SSRF TOCTOU — REAL + documentado en FASE 0.

**Decisión:** Implementar IP pinning (custom httpx transport adapter validando IPs en socket connect time).

**Alternativas:**

| Alternativa | Status | Notas |
|---|---|---|
| IP pinning (transport adapter) | YES | Socket-level validation en connect() |
| Custom resolver usando `aiohttp` | NO — más pesado que FastAPI+httpx |

---

## ADR-006 — SECURITY OPS (clearance enforcement v1) (DECISION)

**Contexto:** N-01 — Clearance enforcement irregular en v1.

**Decisión:** Uniformizar enforcement de clearance en v1 — barrido de todos routers de v1 con tests (SEC-TEST-CLEARANCE-01..08).

**Alternativas:**

| Alternativa | Status | Notas |
|---|---|---|
| Uniformizar enforcement | YES | Fail-closed; tests reales |
| Aceptar risk | NO — security baseline previo |

---

## ADR-007 — MIGRATION vs ALEMBIC (DECISION — VERIFICADO FASE 0: alembic es real)

**Contexto:** migrations/*.legacy vs alembic real.

**Decisión:** Alembic is real (env.py + versions/001_sesis_initial.py + 002_audit_chain.py); legacy files to be archived (FASE 2).

---

## ADR-008 — INFRASTRUCTURE HARDENING (DECISION — FASE 2)

**Contexto:** FASE 0: faltan `infra/ssl/`, `fernet.key`.

**Decisión:**
- Crear `infra/ssl/` con self-signed certs de desarrollo (verficado en FASE 2).
- Crear `fernet.key` vía `scripts/generate_keys.py` + tests (FASE 2).
- Documentar workaround para `docker compose` fallido (falta volúmenes) FASE 2.

---

## ADR-009 — NATS DLQ y workers (DECISION)

**Contexto:** FASE 0 audit: DLQ y idempotencia faltan.

**Decisión:** Implementar DLQ + idempotency keys en NATS (FASE 3). Añadir monitoring alerts.

---

## ADR-010 — CLEARANCE HIERARCHY en Open (DECISION — PARTIAL)

**Contexto:** FASE 0: v1 routers no enforcement clearance.

**Decisión:** Reducir leaks en v1 (fácil, FASE 2). Completar enforcement en todos backends (FASE 5).

---

## ADR-011 — HARDENING MVP (FASE 2)

**Contexto:** TD-006, TD-007, TD-019, TD-020.

**Decisión:** FASE 2 MVP:
- TD-006: EncryptedField fail-closed (fail-fast — researchado)
- TD-007: infra/ssl + fernet.key + docs
- TD-019: X-RateLimit headers + error body + Retry-After
- TD-020: healthzestatic en nginx

---

## ADR-012 — SECURITY HARDENING + SEC-FIX-XXX (FASE 3)

**Contexto:** TD-004, TD-005, HIGH-03, SEC-04.

**Decisión:** FASE 3: SSRF IP pinning, crypto label honesto, docs drift correction, security audit v2.

---

## ADR-013 — DOCS Regeneration (FASE 9)

**Contexto:** docs/* desactualizados, FASE 0 detecta 7 phantom.

**Decisión:** FASE 9: Regenerar docs/{ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md} desde realidad FASE 0.

---

## Índice de ADRs (Registro)

| ADR | Título | Fase Decisión | Escenario | Reversión pendiente |
|---|---|---|---|---|
| ADR-001 | MODULAR MONOLITO vs Microservices | FASE 0 | Decision — implementada por FASE 1 (docs) | — |
| ADR-002 | Layers arquitectónicas | FASE 1 | Architectural decision | Potencial en FASE 2 si breakthrough |
| ADR-003 | User Consolidado | FASE 1 | Architectural decision | Potencial en FASE 4 si bugs encontrados |
| ADR-004 | Auth Consolidado | FASE 1 | Decision | Potencial en FASE 2 si bugs encontrados |
| ADR-005 | SSRF IP Pinning | FASE 1 | Decision | FASE 3 execution |
| ADR-006 | Clearance enforcement v1 | FASE 1 | Decision | FASE 2 execution |
| ADR-007 | Migration vs Alembic | FASE 1 | Decision — Alembic real | — |
| ADR-008 | Infra hardening (ssl/fernet) | FASE 1 | Decision | FASE 2 |
| ADR-009 | NATS DLQ + workers | FASE 1 | Decision | FASE 3 |
| ADR-010 | Clearance Hierarchy Open | FASE 1 | Decision | FASE 5 |
| ADR-011 | MVP Hardening | FASE 1 | Decision | FASE 2 |
| ADR-012 | Security Hardening + SEC-FIX-XXX | FASE 1 | Decision | FASE 3 |
| ADR-013 | Docs regeneration | FASE 1 | Decision | FASE 9 |

---

## Resumen Ejecutivo

Decisiones críticas realizadas en FASE 0-1 (documentadas por ADRs 1-13):
- Modular monolith (ADR-001) — decision altamente fiable
- Layers arquitectónicas (ADR-002)
- User consolidation (ADR-003)
- Auth consolidation (ADR-004)
- SSRF IP pinning (ADR-005)
- Clearance enforcement v1 (ADR-006)
- Alembic vs legacy (ADR-007)
- Infra hardening (ADR-008)
- NATS DLQ (ADR-009)
- MVP hardening (ADR-011)
- Security hardening (ADR-012)
- Docs regeneration (ADR-013)