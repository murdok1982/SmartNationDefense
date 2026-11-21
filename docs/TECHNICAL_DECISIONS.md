# TECHNICAL_DECISIONS.md — Registro de Decisiones Arquitectónicas y Técnicas (SmartNationDefense)

**Doc ID:** TDEC-2026-SND-001 | **Estado:** Registro activo — FASE 0-2

---

## 1. Decisiones Correctas (KPI)

| ID | Decisión | FASE | Alternativa rechazada | Evidence/Validation | Estado |
|---|---|---|---|---|---|
| TDEC-001 | **Modular Monolith** (ADR-001) — no Microservices | FASE 0 | Microservicios (fallible: 3 modelos User collisiones, no justificado en real) | ADR-001 documentado; validado por FASE 1 | `DONE` |
| TDEC-002 | **User Consolidado** — Unified User + IntelUserSchema + OsintUserSchema (ADR-003) | FASE 1 (pending FASE 2) | Namespaceo tables (`intel_users`, `osint_users`) — más rápido FASE 2 | ADR-003 en `docs/architecture/ARCHITECTURE_DECISIONS.md`; impacto real en FASE 2 | `PENDING` (TD-001 — FASE 2) |
| TDEC-003 | **Layers Arquitectónicas** (ADR-002) — Presentation/API/Application/Domain | FASE 1 | Microservices (no) + flat (worse) | ADR-002 documentado | `DONE` |
| TDEC-004 | **Auth Consolidado** — unified router (ADR-004) | FASE 1 (pending FASE 2) | Multiple routers + uniform enforcement (partial FASE 0) | ADR-004 documentado; impacto FASE 2 | `PENDING (TD-003 — FASE 2)` |
| TDEC-005 | **SSRF IP Pinning** (ADR-005, FASE 3) — TOCTOU real HIGH-03 | FASE 3 | Custom transport adapter | ADR-005 + docs/SECURITY_ARCHITECTURE.md FASE 3 | `PENDING (TASK-025)` |
| TDEC-006 | **Clearance enforcement v1** (ADR-006, FASE 2) — uniformizar enforcement v1 + tests | FASE 2 | V2-only + partial v1 (status QUO FASE 0) | ADR-006 documentado; test plan SEC-TEST-CLEARANCE-01..08 | `PENDING (TASK-009, TASK-032)` |
| TDEC-007 | **Alembic vs Legacy** (ADR-007) — Alembic es real, migrations/*.legacy archived | FASE 2 | Legacy as-is, paralelo mezclado | ADR-007 documentado + `alembic heads` FASE 2 | `PENDING (TASK-011)` |
| TDEC-008 | **Infra Hardening** (ADR-008, FASE 2) — infra/ssl + fernet.key + Makefile + docs | FASE 2 | Deploy workaround doc | ADR-008 documentado + Makefile FASE 2 | `PENDING (TASK-017)` |
| TDEC-009 | **NATS DLQ + Idempotency** (ADR-009, FASE 3) — DLQ + idempotency keys | FASE 3 | at-most-once (similar a hoy) | ADR-009 documentado | `PENDING (TASK-028)` |
| TDEC-010 | **Clearance hierarchy Open** (ADR-010, FASE 5) — v1 leaks reduce + v2 complete | FASE 5 | V2-only + partial v1 | ADR-010 documentado | `PENDING (TASK-032, TASK-044)` |
| TDEC-011 | **MVP Hardening** (ADR-011, FASE 2) — EncryptedField fail-closed, X-XSS, healthzestatic | FASE 2 | incremental | ADR-011 documentado + TD-019/TD-020 | `PENDING (TASK-010, TASK-019, TASK-022)` |
| TDEC-012 | **Security Hardening + SEC-FIX-XXX** (ADR-012, FASE 3) — SSRF pinning, crypto labels, HIGH-02, HIGH-03, audit chain persistence | FASE 3 | incremental | ADR-012 documentado + SEC-FIX-XXX list + redteam re-run exit 0 | `PENDING (TASK-024..TASK-029)` |
| TDEC-013 | **Docs regeneration** (ADR-013, FASE 9) — regenerar docs reales | FASE 9 | mantener docs drift | ADR-013 documentado + FASE 9 | `PENDING (TASK-045, TASK-046)` |

---

## 2. Decisiones Incorrectas (Datos reales de FASE 0, seriemt os presentiause en FASE 0 para mejora FASE 2)

| ID | Decisión (incorrecta/controvertida) | Alternativa mejorada | Estado | Notas |
|---|---|---|---|---|
| INC-01 | **Documentar MicroVM Sandbox** en compliance (`compliance/ENS_ALTA_matrix.md`) | Aceptar como EXPERIMENTAL (N-14, FASE 9) | `FIXED — FASE 0` (TASK-001: compliance regenerado + honesto) | FASE 9: regenerar compliance matrices honestas |
| INC-02 | **Aceptar default ADMIN_INITIAL_PASSWORD=admin123** en dev | Desplegar producción con validate_production_hardening + FASE 3 rotate | `PENDING — FASE 3 (TASK-024)` | User preference (dev leniency vs dev/staging) — DOCUMENTAR EXPLICITAMENTE |
| INC-03 | **Aceptar default POSTGRES_PASSWORD=change-me-in-production** | Rotar al deploy de staging/prod (FASE 3) + docs (FASE 9) | `PENDING — FASE 3 (TASK-024)` | |
| INC-04 | **Label "Fernet" como "aes-256-gcm"** (MEDIUM-02) | Labels honestos (Fernet=AES-128-CBC+HMAC) | `PENDING — FASE 3 (TASK-026)` | crypto_quantum.py |
| INC-05 | **Envio Múltiple User models en tabla `users`** | Namespaceo tablas (FASE 2 — intel_users, osint_users) o unified User | `PENDING — FASE 2 (TASK-008, TD-001)` | |
| INC-06 | **Fail-open rate limiting** (N-02) | Disable open circuit + documentar + circuit breaker FASE 2 | `PENDING — FASE 2 (TASK-013) + Accepted-Risk (TD-010)` | |
| INC-07 | **`docs/SECURITY_AUDIT.md` incompleto** (C01/C02 downgraded, no C02 details) | Nuevo SECURITY_AUDIT.md real FASE 0 | `FIXED — FASE 0` | |
| INC-08 | **X-XSS-Protection deprecado (MDN rss)** | Remove + Permissions-Policy explícito (FASE 2) | `PENDING — FASE 2 (TASK-019)` | |
| INC-09 | **ssh-keynar): Abelas em ASC emAXMU No Final** | No-reporting + notas (FASE 9) | `FIXED — FASE 0` (TASK-001, TASK-046) | |

---

## 3. Decisiones Plausibles (Ángulos de cambio, FASE 2+)

| ID | Decisión | Categoría | FASE Preference |
|---|---|---|---|
| PLA-01 | Microservices (N/A — user prefere Modular) | Arquitectura | N/A |
| PLA-02 | PostgreSQL-Only (Sin MySQL, Sin Oracle) | Data | FASE 2 |
| PLA-03 | Redis/NATS como bus de eventos (vs Kafka) | Infra | FASE 2/3 |
| PLA-04 | PostgreSQL 16 + pgvector (N/A) | Data | N/A |
| PLA-05 | Ollama vs OpenAI (vs LM Studio) | AI | FASE 3 |
| PLA-06 | Texto vs ML para COA/Fusion (vs reglas) | Fusion | FASE 2-4 |
| PLA-07 | REST API (vs GraphQL) | API | FASE 3 |

---

## 4. Notas de Referencia

- Todas las decisiones documentadas en `.factory/ARCHITECTURE.md` (FASE 0-1) — ADR-001..013.
- Todas las decisiones de FASE 2+ documentadas en `.factory/TASKS.md` — TASK-008..TASK-046 (Owner, Spec Ref, Target Files, Verification, Retries).
- Verificación real FASE 2-5 por `@qa-verifier` con commandos reales + evidence.
- Referencia: FASE 0 — `docs/audit/*`, FASE 1 — `docs/architecture/*`, FASE 2+ — `docs/architecture/*`, `.factory/*`, `docs/{TRANSFORMATION_PROGRESS,TECHNICAL_DECISIONS}.md`.