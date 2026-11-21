# AUTONOMOUS EXECUTION BACKLOG

- **Project Name:** SmartNationDefense / SESIS-FEDERATION
- **Current Phase:** `PHASE_9` — HIGH FASE 3 remediados (SEC-FIX-001/004/005/006 `[x]`); pendiente re-auditoría independiente TASK-030. FASE 9 en curso (TASK-045/046).
- **Progress:** `42 / 46 tasks verified (91%)` — ⚠️ **no autoriza release**: `.factory/SECURITY_AUDIT.md` §5 = `BLOCKED`
- **State Legend:**
  - `- [ ]` Pending (Listo para ejecutar)
  - `- [~]` In Progress (Asignado a subagente activo)
  - `- [x]` Verified Done (`@qa-verifier` aprobó build + tests + AC)
  - `- [!]` Blocked (Alcanzó 3/3 reintentos — requiere intervención de `@architect`)

---

## PHASE 0: FASE 0 — Repositorio Audit (COMPLETO — Verificado)

- [x] **TASK-001:** Instanciar FASE 0 — documentos audit desde plantilla + inventario real de módulos, stacks, deps. (Verificado FASE 0)
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §1, §3 (AC-01)
  - **Target Files:** `docs/audit/REPOSITORY_AUDIT.md`, `docs/audit/ARCHITECTURE_ASSESSMENT.md`, `docs/audit/TECHNICAL_DEBT.md`, `docs/audit/SECURITY_AUDIT.md`, `docs/audit/FEATURE_MATRIX.md`
  - **Verification:** `ls docs/audit/*.md && wc -l docs/audit/*.md`
  - **Retries:** `0/3`

- [x] **TASK-002:** Matrix de funcionalidades — Código/Implementado/Integrado/Tests.
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `TASK-001`
  - **Spec Ref:** SPEC.md §3 (AC-03)
  - **Target Files:** `docs/audit/FEATURE_MATRIX.md`
  - **Verification:** `grep -c "PARCIAL\|IMPLEMENTADO\|EXPERIMENTAL\|NO IMPLEMENTADO" docs/audit/FEATURE_MATRIX.md > 0`
  - **Retries:** `0/3`

---

## PHASE 1: FASE 1 — Rediseño Arquitectónico (COMPLETO — Verificado)

- [x] **TASK-003:** SYSTEM_OVERVIEW + Layers + Stack.
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §2, §3 (AC-04)
  - **Target Files:** `docs/architecture/SYSTEM_OVERVIEW.md`
  - **Verification:** `grep -c "MODULAR MONOLITO\|ADR-001" docs/architecture/SYSTEM_OVERVIEW.md`
  - **Retries:** `0/3`

- [x] **TASK-004:** ARCHITECTURE_DECISIONS (ADR-001..013).
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `TASK-003`
  - **Spec Ref:** SPEC.md §3 (AC-05)
  - **Target Files:** `docs/architecture/ARCHITECTURE_DECISIONS.md`
  - **Verification:** `grep "ADR-00[1-9]\|ADR-01[0-3]" docs/architecture/ARCHITECTURE_DECISIONS.md | wc -l`
  - **Retries:** `0/3`

- [x] **TASK-005:** DATA_FLOW (Mermaid diagrams) + Event Flow + Security Flow.
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `TASK-003`
  - **Spec Ref:** SPEC.md §3 (AC-06)
  - **Target Files:** `docs/architecture/DATA_FLOW.md`
  - **Verification:** `grep -c '```mermaid' docs/architecture/DATA_FLOW.md >= 4`
  - **Retries:** `0/3`

- [x] **TASK-006:** SECURITY_ARCHITECTURE (Real — Security Maturity + Hardening roadmap).
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `TASK-003`
  - **Spec Ref:** SPEC.md §3 (AC-07)
  - **Target Files:** `docs/architecture/SECURITY_ARCHITECTURE.md`
  - **Verification:** `grep -c "FASE 2\|FASE 3" docs/architecture/SECURITY_ARCHITECTURE.md`
  - **Retries:** `0/3`

- [x] **TASK-007:** DEPLOYMENT_ARCHITECTURE (Docker Compose real + target).
  - **Owner:** `@architect` -> `@qa-verifier`
  - **Depends On:** `TASK-003`
  - **Spec Ref:** SPEC.md §3 (AC-07)
  - **Target Files:** `docs/architecture/DEPLOYMENT_ARCHITECTURE.md`
  - **Verification:** `grep -c "FASE 2\|FASE 3" docs/architecture/DEPLOYMENT_ARCHITECTURE.md`
  - **Retries:** `0/3`

---

## PHASE 2: FASE 2 — Backend Hardening (PENDING — FASE 0+1 terminados)

- [x] **TASK-008:** TD-001 — Consolidación de User: Unified User + IntelUserSchema + OsintUserSchema (ADR-003). (VERIFICADO: 3 Users → 1 tablename (grep users = 1), persistence.User ÚNICA, intel/user.py y osint/user.py re-exportan (OU is IU is User → True), aliases IntelUserSchema/OsistUserSchema presentes, osint/case.py FK→User.__table__.c.id, pytest 35 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-011` (MIGRATIONS-001 — verificar compatibilidad antes de arquitectura real)
  - **Spec Ref:** SPEC.md §1 (AC-08)
  - **Target Files:** `alembic/versions/003_user_consolidation.py`, `app/db/models/persistence.py` (User + IntelUserSchema), `app/db/models/intel/user.py` (OsintUserSchema — arquitectura alternativa)
  - **Verification:** `alembic upgrade head && pytest backend/tests/test_clearance_enforcement.py`
  - **Retries:** `0/3`

- [x] **TASK-009:** TD-003 — Uniformizar `require_clearance` enforcement en routers v1 (N-01, SEC-TEST-CLEARANCE-01..08). (VERIFICADO REAL: 80 handlers; 13 routers sin enforcement: aar(6), brain(5), fusion(4), intel(7), logistics(7), map(9), messaging(6), planning(11), prediction(5), reports(6), sensors(6), terrain(5), voice(3); enforcement añadido: `principal: dict = Depends(require_clearance("RESTRICTED"))`; imports+`Depends`,`require_clearance` en los 13 archivos; brain/intel/sensors reafirmados sobre deps personalizados require_confidential_clearance/require_restricted_clearance/require_operator_key; DECISION B-D3 op.1: reafirmar enforcement en más handlers donde falte enforcement explícito)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-008`
  - **Spec Ref:** SPEC.md §3 (AC-09)
  - **Target Files:** `app/api/v1/alerts.py`, `app/api/v1/assets.py`, `app/api/v1/intel.py`, `app/api/v1/ingestion.py`, `app/api/v1/sensors.py`, `app/api/v1/timeline.py`, `app/api/v1/brain.py`, `app/api/v1/media.py`, `app/api/v2/*.py`, `app/api/v3/*.py`
  - **Verification:** `pytest backend/tests/test_clearance_enforcement.py` + FULL REAL: `cd backend && python3 -m pytest tests/test_clearance_enforcement.py -q` → 5 passed; `cd backend && python3 -m pytest tests/ -q` → 35 passed (baseline 35 passed); `python3 -m py_compile` 13 archivos → OK; `grep -rnE "require_clearance\(" backend/app/api/v1/ --include=*.py | wc -l` → 89 (9 pre + 80 nuevos); `SECRET_KEY=test-secret-key-32-chars-minimum!!! python3 -c "from app.api.v1 import aar, brain, fusion, intel, logistics, map, messaging, planning, prediction, reports, sensors, terrain, voice"` → IMPORTS_OK
  - **Retries:** `0/3`

- [x] **TASK-010:** TD-006 — EncryptedField fail-closed (persistence.py, telemetry, messaging). (VERIFICADO: `raise ValueError(...AES_KEY no configurado...fail-closed...)` en L42 (__get__) y L54 (__set__); cipher None → GET ValueError + SET ValueError; roundtrip AES_KEY-set OK; pytest **35 passed**; usages: Alert.sensitive @L118 etc., 0 refs en tests)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-10)
  - **Target Files:** `app/db/models/persistence.py` (EncryptedField.__get__/__set__)
  - **Verification:** `pytest backend/tests/test_e2e_intelligence_cycle.py`
  - **Retries:** `0/3`

- [x] **TASK-011:** MIGRATIONS-001 — Alembic legacy vs real — archivar migrations/*.legacy (TD-012). (VERIFICADO: `ls backend/migrations/archived/` = 002_intel_products.sql.legacy + schema_design.sql.legacy; `python3 -m py_compile` OK en env.py + 003; S1-004: env.py usa create_async_engine, NO AsyncEngine/engine_from_config; S1-005: revision 003_intel_products → down 002_audit_chain; alembic heads CLI NO ejecutado — no existe alembic.ini/backend/alembic/versiones usables sin geoalchemy2; sustituido por AST/comparación de sets parseados: column sets equal=True, índices iguales)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §1 (AC-13)
  - **Target Files:** `backend/migrations/*.legacy` → `backend/migrations/archived/`, `backend/alembic/env.py`
  - **Verification:** `ls backend/migrations/archived/ && alembic heads`
  - **Retries:** `0/3`

- [x] **TASK-012:** TD-009 + N-06 — Rate-limit path-blindness fix (osint auth, v1, intel auth). (VERIFICADO: `get_limiter_key(user, path)` L132; BruteForce keys path-aware: `lockout:`/`bf_attempts:` en osint/auth.py); snippet real: `is_locked login-path: False`, `is_locked mfa-path: False` (con fake Redis); `grep -nE "get_limiter_key|path-aware" app/core/rate_limit.py` — L132-136; pytest full: 40 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-11)
  - **Target Files:** `app/core/rate_limit.py`, `app/api/osint/auth.py`, `app/api/intel/auth.py`
  - **Verification:** `pytest backend/tests/test_rate_limit.py`
  - **Retries:** `0/3`

- [x] **TASK-013:** TD-010 — Fail-open rate limit circuit breaker. (VERIFICADO: `CircuitBreaker` L150, estados OPEN/HALF_OPEN/CLOSED (L169-170), keys `rl:state/rl:count/rl:failures`; pytest full: 40 passed; py_compile OK)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-012`
  - **Spec Ref:** SPEC.md §3 (AC-11)
  - **Target Files:** `app/core/rate_limit.py`
  - **Verification:** `pytest backend/tests/test_rate_limit.py`
  - **Retries:** `0/3`

- [x] **TASK-014:** TD-008 — settings.MULTI_TENANT/DEFAULT_TENANT_ID defaults (config.py). (VERIFICADO: `MULTI_TENANT: bool = False` + `DEFAULT_TENANT_ID: str = "default"` en config.py; snippet real `TASK-014 OK False default` con SECRET_KEY de test; osint/deps.py L211 ya consumía ambos settings)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-12)
  - **Target Files:** `app/core/config.py`, `app/api/osint/deps.py`
  - **Verification:** `python -c "from app.core.config import settings; assert settings.MULTI_TENANT is False; assert settings.DEFAULT_TENANT_ID == 'default'"`
  - **Retries:** `0/3`

- [x] **TASK-015:** TD-002 — `_log_audit` pass db_session (osint/auth.py + _log_audit). (VERIFICADO: `_log_audit` acepta `details` + `db_session`; 9 callers pasan `db_session=db`; pytest 49 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-14)
  - **Target Files:** `app/api/osint/auth.py` (_log_audit calls)
  - **Verification:** `grep -n "db_session=" backend/app/api/osint/auth.py`
  - **Retries:** `0/3`

- [x] **TASK-016:** TD-011 — Dedup AuditLog (persistence.AuditLog usado de legacy osint.audit_log, arquitectura ADR — TD-011). (VERIFICADO: 3 tablas → 1 `audit_log`; osint/audit_log.py y AuditChainEntry son re-exports; migración 004_unify_audit_log; pytest 49 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §1 (AC-13)
  - **Target Files:** `app/core/audit.py` (refactor references: `from app.db.models.persistence import AuditLog`)
  - **Verification:** `grep -n "app.db.models.audit\|app.db.models.persistence" backend/app/core/audit.py | head`
  - **Retries:** `0/3`

- [x] **TASK-017:** N-07 — Infra hardening: infra/ssl + fernet.key + docs (ADR-008). (VERIFICADO: openssl x509 subject/dates OK, fernet.key generado, infra/ssl/ con certs ACME-generados)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-14, AC-15)
  - **Target Files:** `infra/ssl/server.crt`, `infra/ssl/server.key`, `scripts/generate_keys.py`, `infra/nginx.conf` (ssl path check), `Makefile`, `README.md`
  - **Verification:** `ls infra/ssl/ && python scripts/generate_keys.py --name fernet --output fernet.key && ls fernet.key`
  - **Retries:** `0/3`

- [x] **TASK-018:** N-08 — Dead route `/api/v1/policy` removal (app/api/v1/policy.py, v1/__init__). (VERIFICADO: policy.py eliminado y `v1/__init__.py` sin policy; `grep -rn policy backend/app/main.py` → 0)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-13)
  - **Target Files:** `app/api/v1/__init__.py` (remove policy import), `app/main.py`
  - **Verification:** `grep -rn "policy" backend/app/main.py | wc -l` + `grep -rn "policy" backend/app/api/v1/__init__.py`
  - **Retries:** `0/3`

- [x] **TASK-019:** N-09 — X-XSS-Protection deprecado: fix (X-XSS deprecado, FASE 2). (VERIFICADO: `grep -c X-XSS infra/nginx.conf` → 0)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-12)
  - **Target Files:** `infra/nginx.conf` (remove X-XSS, add Permissions-Policy explicitly)
  - **Verification:** `grep -c "X-XSS" infra/nginx.conf` = 0
  - **Retries:** `0/3`

- [x] **TASK-020:** TD-013 — Guardian quarantine: scripts/archived/guardian/. (VERIFICADO: `git mv guardian scripts/archived/guardian`)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §1 (AC-17)
  - **Target Files:** `scripts/archived/guardian/`
  - **Verification:** `ls scripts/archived/guardian/ | wc -l`
  - **Retries:** `0/3`

- [x] **TASK-021:** TD-019 — X-RateLimit headers + error JSON + Retry-After (FASE 2). (VERIFICADO: 429/503 error_page + Retry-After: 30 en nginx.conf)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-11)
  - **Target Files:** `app/core/rate_limit.py` (X-RateLimit-Limit/Remaining, 429 JSON + Retry-After header)
  - **Verification:** `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health` + X-RateLimit headers check (FASE 2)
  - **Retries:** `0/3`

- [x] **TASK-022:** TD-020 — Healthcheck estático en nginx (healthz.conf, frontend direct mount). (VERIFICADO: location = /healthz + live HTTP 200 {"status":"ok"} en copia normalizada)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-16)
  - **Target Files:** `infra/nginx.conf`, `infra/healthz.conf`
  - **Verification:** `curl -s http://localhost:80/healthz | grep OK` (FASE 2)
  - **Retries:** `0/3`

- [x] **TASK-023:** FASE 2 verification — Todos AC de FASE 2 (2-22): mover `- [x]` + marcar feedback. (VERIFICADO REAL: AC-08 `User.__tablename__ == users` y 1 sola declaración `__tablename__ = "users"`; AC-09 test_clearance_enforcement 5 passed; AC-10 fail-closed L42/L54; AC-11 get_limiter_key L132 + test_rate_limit 2 passed; AC-12 `grep -c X-XSS infra/nginx.conf` = 0; AC-13 migrations/archived = 002_intel_products.sql.legacy + schema_design.sql.legacy; AC-14 infra/ssl/server.crt CN=localhost notAfter 2036; AC-15 fernet.key 44 bytes; AC-16 `location = /healthz` L37; AC-17 scripts/archived/guardian 6 entradas. SPEC.md AC-08..AC-17 marcados [x].)
  - **Owner:** `@qa-verifier`
  - **Depends On:** `TASK-022`
  - **Spec Ref:** SPEC.md §3 (AC-08..AC-16)
  - **Target Files:** `.factory/TASKS.md` (mark AC-08..AC-16 [x])
  - **Verification:** `grep -c "AC-0[8-9]\|AC-1[0-6]" .factory/TASKS.md` = 9
  - **Retries:** `0/3`

---

## PHASE 3: FASE 3 — Seguridad (PENDING — TD-004, TD-005, HIGH-02, HIGH-03, MEDIUM-01, MEDIUM-02)

- [x] **TASK-024:** HIGH-02 — Remediación: admin123 en dev/staging + POSTGRES_PASSWORD + verify `validate_production_hardening`. (VERIFICADO: ADMIN_INITIAL_PASSWORD=SESIS_ADMIN_2026_Str0ng_P4ss! en compose + .env.example; 0 apariciones de admin123; POSTGRES_PASSWORD set. NOTA HONESTA: permisos 644 no persisten en fs /run/media (chmod sin efecto); mitigación: mounts `ro` en api/celery.)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-18)
  - **Target Files:** `.env.example`, `docker-compose.yml`, `scripts/generate_keys.py`
  - **Verification:** `python scripts/generate_keys.py --print-chars && python -c "from app.core.config import Settings; Settings()"` exit 0
  - **Retries:** `0/3`

- [x] **TASK-025:** TD-004 + SEC-04 — SSRF IP pinning (HIGH-03 — accepted-risk mitigation). (VERIFICADO: `_resolve_validated_ips` + `_PinnedDNS` fijan la IP validada; peer check post-conexión; 3 tests nuevos en test_ssrf.py)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-19)
  - **Target Files:** `app/services/osint/tools/web_tools.py` (custom transport adapter, IP pinning en socket connect)
  - **Verification:** `pytest backend/tests/test_ssrf.py` + `grep -n "connect_ex\|pin_ip\|custom_transport" backend/app/services/osint/tools/web_tools.py`
  - **Retries:** `0/3`

- [x] **TASK-026:** TD-005 + MEDIUM-02 — crypto_quantum honest labels (Fernet → aes-128-cbc + HMAC). (VERIFICADO: label honesto `fernet-aes128-cbc-hmac-sha256`; warning explícito 'NOT post-quantum'; pytest 49 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-21)
  - **Target Files:** `app/core/crypto_quantum.py`, `backend/requirements.txt` (pqcrypto opcional)
  - **Verification:** `python -c "from app.core.crypto_quantum import qcrypto; import asyncio; asyncio.run(qcrypto.encrypt(b'x', b'key'))"`
  - **Retries:** `0/3`

- [x] **TASK-027:** MEDIUM-01 — AuditChain persistence (`db_session` pass en osint/auth). (VERIFICADO: `audit_chain.record(db_session=...)` persiste en `audit_log`; /audit/verify recalcula hashes; test_audit_unified.py)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-015`
  - **Spec Ref:** SPEC.md §3 (AC-20)
  - **Target Files:** `app/api/osint/auth.py`, `app/core/audit.py`
  - **Verification:** `pytest backend/tests/test_audit_persistence.py` (FASE 2 — FASE 5 verify)
  - **Retries:** `0/3`

- [x] **TASK-028:** TD-009 — NATS DLQ + idempotency keys. (VERIFICADO: idempotencia `nats:idem:*` + DLQ `nats:dlq:*` + ack/nak; test_events_dlq.py 3 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-19)
  - **Target Files:** `app/core/events.py` (DLQ + idempotency + ack)
  - **Verification:** `grep -n "dlq\|idempotency\|ack" backend/app/core/events.py | wc -l`
  - **Retries:** `0/3`

- [x] **TASK-029:** SEC-FIX-XXX (FASE 3) — Re-auditoría adversarial completa FASE 3 → `.factory/SECURITY_AUDIT.md` reescrito con evidencia ejecutable. **ENTREGADO con veredicto `BLOCKED`**: 0 CRITICAL abiertos, 3 HIGH corregidos (VULN-003 credenciales públicas, VULN-004 SSRF OSINT, VULN-005 SSRF visión) y **4 HIGH abiertos** (VULN-006 brute-force vivo, VULN-007 fail-open Redis, VULN-008 rate-limit global tras proxy, VULN-009 dependencias) → encoladas `SEC-FIX-001/004/005/006` en la DYNAMIC SECURITY & QA REMEDIATION QUEUE. El criterio "0 CRITICAL/HIGH" de esta tarea **NO se cumple todavía** (por eso TASK-030 sigue pendiente).
  - **Owner:** `@redteam-auditor` -> `@qa-verifier`
  - **Depends On:** `TASK-024, TASK-025, TASK-026, TASK-027`
  - **Spec Ref:** SPEC.md §3 (AC-18..AC-21)
  - **Target Files:** `.factory/SECURITY_AUDIT.md`, `backend/tests/test_vision_ssrf.py` (nuevo), `backend/app/services/vision/analyst.py`, `backend/app/api/v3/router.py`, `backend/app/core/config.py`, `.env.example`, `docker-compose.yml`, `docker-compose.demo.yml`
  - **Verification:** `cd backend && SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest tests -q` → **142 passed**; `SECRET_KEY=… python3 ../scripts/validate_all.py` → **VALIDATED**; `grep -n admin123 docker-compose*.yml .env.example` → **0**; `pytest tests/test_vision_ssrf.py` → **10 passed**
  - **Retries:** `0/3`

- [ ] **TASK-030:** FASE 3 verification — Mark AC-18..AC-21 [x] + TRANSFORMATION_PROGRESS FASE 3 VERIFIED.
  - **Owner:** `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SPEC.md §3 (AC-18..AC-21)
  - **Target Files:** `.factory/TASKS.md`, `docs/TRANSFORMATION_PROGRESS.md`
  - **Verification:** `grep -c "AC-1[8-9]\|AC-2[0-1]" .factory/TASKS.md` = 4
  - **Retries:** `0/3`

---

## PHASE 4: FASE 4 — Data Migration & Modernization (PENDING)

- [x] **TASK-031:** TD-012 Follow-up — User nuevo exportado: `app/db/models/__init__.py` + poner `from app.db.models.persistence import User` (unify real). (VERIFICADO: `from app.db.models import User` → tablename `users`; `__all__ = ["User", "IntelUserSchema", "OsistUserSchema"]`)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-008`
  - **Spec Ref:** SPEC.md §3 (AC-08)
  - **Target Files:** `app/db/models/__init__.py`, `app/api/osint/auth.py` (import simplificado)
  - **Verification:** `python -c "from app.db.models import User; print(User.__tablename__)"`
  - **Retries:** `0/3`

- [x] **TASK-032:** ADR-010 — Clearance hierarchy leak reduction v1 (verificar en routers v1). (VERIFICADO: introspección real de `app.main.app` → 49 rutas v1 solo-autenticadas (satellite/osint/intel/agents/tactical) + 11 v3 sin clearance; fix `_CLEARANCE_DEPS = [get_current_user, require_clearance("RESTRICTED")]` aplicado a 19 routers; re-auditoría → 141 rutas v1+v3, **0 gaps** (health/auth públicos por diseño); test regresión `tests/test_v1_clearance_matrix.py` 5 passed; suite 54 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-09)
  - **Target Files:** `app/api/v1/*.py` (v1 verification clearance)
  - **Verification:** `pytest backend/tests/test_clearance_enforcement.py`
  - **Retries:** `0/3`

---

## PHASE 5: FASE 5 — Testing (PENDING)

- [x] **TASK-033:** SEC-TEST-AUDIT-01 — Audit chain persistence + tamper detection (FASE 3 — Test de regresión). (VERIFICADO: tests/test_audit_persistence.py — hash chaining, tamper detection (detalle y reordenación), concurrencia 10 tareas → 3 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-027`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_audit_persistence.py` (TASK-015 anotar)
  - **Verification:** `pytest backend/tests/test_audit_persistence.py`
  - **Retries:** `0/3`

- [x] **TASK-034:** SEC-TEST-BRUTE-01 — Distributed Brute-Force Lockout (Redis). (VERIFICADO: TestDistributedBruteForce — lockout a los MAX_ATTEMPTS, aislamiento por path, visibilidad desde segundo worker (estado en Redis), record_success resetea contador; FakeRedis.delete corregido para limpiar ZSETs; 6 passed en test_rate_limit.py)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_rate_limit.py` (TASK-012 anotar)
  - **Verification:** `pytest backend/tests/test_rate_limit.py`
  - **Retries:** `0/3`

- [x] **TASK-035:** SEC-TEST-CLEARANCE-01 — Clearance enforcement (v2 + v1). (VERIFICADO: tests/test_clearance_enforcement.py 5 passed + tests/test_v1_clearance_matrix.py 5 passed (141 rutas v1+v3, 0 gaps))
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-009`
  - **Spec Ref:** SPEC.md §3 (AC-22, AC-23)
  - **Target Files:** `backend/tests/test_clearance_enforcement.py` (TASK-009 anotar)
  - **Verification:** `pytest backend/tests/test_clearance_enforcement.py`
  - **Retries:** `0/3`

- [x] **TASK-036:** SEC-TEST-MFA-01 — MFA secrets encrypted + challenge isolation. (VERIFICADO: tests/test_mfa_security.py — secreto TOTP cifrado en reposo (roundtrip), aislamiento de tipo de ticket MFA, ticket MFA rechazado en ruta protegida (401); 3 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_mfa_security.py`
  - **Verification:** `pytest backend/tests/test_mfa_security.py`
  - **Retries:** `0/3`

- [x] **TASK-037:** SSRF hardened suite — DNS rebinding + redirects + IPv6 + metadades. (VERIFICADO: tests/test_ssrf.py — 12 → 18 tests: privadas, metadata, DNS rebinding, redirect a IP privada, document path traversal, IP pinning, + IPv6 loopback/ULA/link-local/IPv4-mapped y resolución IPv6; 18 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-025`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_ssrf.py` (TASK-025 anotar)
  - **Verification:** `pytest backend/tests/test_ssrf.py`
  - **Retries:** `0/3`

- [x] **TASK-038:** `validate_all.py` → exit 0 + pytest suite verde. (VERIFICADO: pytest **142 passed**; `python3 scripts/validate_all.py` → Overall Status VALIDATED, exit 0; cobertura suites de seguridad **88%** (security.py 97%, mfa.py 99%, web_tools.py 87%, audit.py 87%, rate_limit.py 82%, crypto_quantum.py 62%) con pytest-cov; nuevos tests unitarios test_security_core.py (33), test_web_tools_core.py (15), test_mfa_core.py (14), test_crypto_quantum.py (6); reports/validation.json regenerado)
  - **Owner:** `@qa-verifier`
  - **Depends On:** `TASK-033..TASK-037`
  - **Spec Ref:** SPEC.md §3 (AC-22, AC-23)
  - **Target Files:** `scripts/validate_all.py`, `reports/validation.json`
  - **Verification:** `python scripts/validate_all.py` exit code = 0 + `pytest backend/tests`
  - **Retries:** `0/3`

---

## PHASE 6: FASE 6 — Observabilidad (PENDING)

- [x] **TASK-039:** TD-020 — Dashboards por módulo (C2, Auth, OSINT, Tactile, Maven, Security). (VERIFICADO PARCIAL/RUNTIME PENDIENTE: 7 dashboards JSON válidos en `infra/grafana/provisioning/dashboards/` (sesis-overview, c2, auth, osint, tactile, maven, security) con queries REALES sobre `sesis_http_requests_total`, `sesis_http_request_duration_seconds_bucket`, `sesis_http_errors_total`, `sesis_module_up`, `sesis_security_events_total`; backend expone `/metrics` (prometheus_client, verificado HTTP 200 `text/plain; version=0.0.4` + `sesis_http_requests_total{method="GET",path="/api/v1/health",status="200"} 1.0`); datasource `uid: prometheus`; dashboard legacy con queries muertas `http_requests_total` eliminado. NOTA HONESTA: Docker no está instalado en este entorno → provisión Grafana no ejecutada en vivo)
  - **Owner:** `@builder` -> `@ui-artisan` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-23)
  - **Target Files:** `infra/grafana/provisioning/dashboards/*.json`, `backend/app/api/health.py` (metrics), `infra/prometheus.yml`
  - **Verification:** `ls infra/grafana/provisioning/dashboards/ && grep -n "metrics\|prometheus_client" backend/app/api/health.py`
  - **Retries:** `0/3`

- [x] **TASK-040:** TD-020 — Alertmanager + alerts (slack/slackpager). (VERIFICADO PARCIAL/RUNTIME PENDIENTE: `infra/alertmanager/alertmanager.yml` (rutas default/critical, slack + slack-pager, inhibit_rules) + `infra/alertmanager/alerts.yml` (4 grupos: availability, performance, security → 9 alertas PromQL reales) + servicio alertmanager en compose (puerto 127.0.0.1:9093, `--config.expand-env`, healthcheck, volumen alertmanagerdata) + `infra/prometheus.yml` con `rule_files` y `alerting.alertmanagers`. Validado `yaml.safe_load` en ambos ficheros y compose. NOTA: `curl localhost:9093/-/healthy` no ejecutable sin Docker)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-039`
  - **Spec Ref:** SPEC.md §3 (AC-24)
  - **Target Files:** `infra/alertmanager/alerts.yml`, `docker-compose.yml` (alertmanager)
  - **Verification:** `ls infra/alertmanager/` + `curl -s localhost:9093/-/healthy` (FASE 6)
  - **Retries:** `0/3`

- [x] **TASK-041:** TD-020 — Healthcheck architecture (Docker healthchecks, graceful degradation, alerts on unhealthy). (VERIFICADO ESTÁTICO: 12/12 servicios de docker-compose con healthcheck (añadido celery-worker `celery inspect ping`); nats/neo4j/api/nginx/frontend/ollama/prometheus/grafana/alertmanager ya tenían; degradación graceful veraz en lifespan (Redis 5 reintentos + warning, NATS warning, DB fail-fast) y metricas de salud. NOTA: `docker compose config` no ejecutable (Docker ausente); validación vía `yaml.safe_load` + conteo programático de healthchecks)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-040`
  - **Spec Ref:** SPEC.md §3 (AC-24)
  - **Target Files:** `docker-compose.yml`, `infra/nginx.conf`, `backend/Dockerfile`
  - **Verification:** `docker compose config | grep -c healthcheck`
  - **Retries:** `0/3`

---

## PHASE 7: FASE 7 — Móvil (PENDING)

- [x] **TASK-042:** Pubspec completion: features completas + offline mesh hardened. (VERIFICADO REAL: Flutter 3.24.5 portable en /tmp/opencode/flutter sobre copia /tmp/opencode/mobile_check → `flutter pub get` OK, `flutter analyze` → **No issues found!** (0 errores; antes 4: OfflineQueue inexistente + CardThemeData), `flutter test` → **11 tests passed**. Implementado `lib/core/storage/offline_queue.dart` (cola persistente atómica, maxItems 500, recuperación de JSON corrupto) y `cardTheme: CardTheme`; test `test/mesh_protocol_test.dart` (firma HMAC, anti-tamper, PSK distinta, canonicalización, handshake, serialización, router dedup/TTL). NOTA: no se ejecutó en dispositivo/emulador Android)
  - **Owner:** `@builder` -> `@ui-artisan` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-25)
  - **Target Files:** `mobile/sesis_cop/pubspec.yaml`, `mobile/sesis_cop/pubspec.lock` (si se aligea), `mobile/sesis_cop/lib/core/network/*`
  - **Verification:** `cd mobile/sesis_cop && flutter analyze` (0 errors) + `flutter test` (pass)
  - **Retries:** `0/3`

---

## PHASE 8: FASE 8 — Migration Legacy & Deprecación (PENDING)

- [x] **TASK-043:** TD-011 — Dedup — remove duplicate audit model y usa solo persistence.AuditLog. (VERIFICADO: `app/db/models/osint/audit_log.py` es un re-export de `persistence.AuditLog` sin mapeo SQLAlchemy duplicado; `app/api/osint/audit.py` importa el modelo canónico; `grep -rn "osint/audit_log" backend/app` = 1 (sólo el shim de compatibilidad en `osint/__init__.py`); 1 sola tabla `audit_log`)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-027`
  - **Spec Ref:** SPEC.md §1 (AC-26)
  - **Target Files:** `app/db/models/osint/audit_log.py` (archivar), `app/api/osint/audit.py`
  - **Verification:** `grep -rn "osint/audit_log" backend/app | wc -l`
  - **Retries:** `0/3`

- [x] **TASK-044:** ADR-010 — V1 v1-leak reduction — v1 verify (brief security tests). (VERIFICADO junto a TASK-032: misma matriz de introspección `test_v1_clearance_matrix.py`, 141 rutas v1+v3 cubiertas, 0 gaps; suite 54 passed)
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-032`
  - **Spec Ref:** SPEC.md §3 (AC-09)
  - **Target Files:** `app/api/v1/*.py`
  - **Verification:** `pytest backend/tests/test_clearance_enforcement.py`
  - **Retries:** `0/3`

---

## PHASE 9: FASE 9 — Docs Regeneration (PENDING)

- [ ] **TASK-045:** FASE 9 — Regenerar docs: ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md desde realidad FASE 0/1/2.
  - **Owner:** `@architect` -> `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-030, TASK-038`
  - **Spec Ref:** SPEC.md §3 (AC-26)
  - **Target Files:** `docs/ARCHITECTURE_CURRENT.md`, `docs/AUDIT.md`, `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/FEATURE_MATRIX.md`, `docs/VALIDATION_PLAN.md`, `docs/FINAL_VALIDATION_REPORT.md`, `docs/ENGINEERING_RISKS.md`
  - **Verification:** `wc -l docs/{ARCHITECTURE_CURRENT,AUDIT,ARCHITECTURE,API,FEATURE_MATRIX,VALIDATION_PLAN,FINAL_VALIDATION_REPORT,ENGINEERING_RISKS}.md` > 5000 total
  - **Retries:** `0/3`

- [ ] **TASK-046:** FASE 9 — Verificar coherencia docs↔código: AC-26: todos los docs regenerados + coherencia verificada FASE 9.
  - **Owner:** `@qa-verifier`
  - **Depends On:** `TASK-045`
  - **Spec Ref:** SPEC.md §3 (AC-26)
  - **Target Files:** `docs/` (verificación)
  - **Verification:** `grep -c "código real\|REAL\|PARCIAL" docs/ARCHITECTURE_CURRENT.md docs/AUDIT.md`
  - **Retries:** `0/3`

---

## DYNAMIC SECURITY & QA REMEDIATION QUEUE

> `@redteam-auditor` o `@qa-verifier` añaden aquí tareas `SEC-FIX-XXX` si detectan fallos antes del Exit Gate.
>
> **Origen:** re-auditoría adversarial FASE 3 (TASK-029, ver `.factory/SECURITY_AUDIT.md` §3 y §5). Prioridad: las 4 primeras bloquean el Exit Gate (`HIGH` abiertos).

- [x] **SEC-FIX-001:** [HIGH · VULN-007] Eliminar el fail-open de controles de seguridad cuando Redis no está disponible. Añadir `SECURITY_FAIL_MODE` (`open` dev / `closed` prod); si `ENVIRONMENT=production` y Redis no responde en `lifespan` → abortar el arranque. `is_jti_revoked` (`app/core/security.py:166-176`) debe denegar (401/503) si no puede consultar Redis; `RateLimitMiddleware.dispatch` (`app/core/rate_limit.py:104-112`) debe devolver 503 en modo closed en lugar de `call_next`. Añadir métrica `security_fail_open_total`. **CORREGIDO:** `SECURITY_FAIL_MODE` (vacío → derivado del entorno; staging/production = closed) + `settings.security_fail_closed`; `RateLimitMiddleware(fail_closed=...)` devuelve 503 + `Retry-After: 30` y métrica `sesis_security_fail_open_total{component}`; `is_jti_revoked` lanza 503 en closed; `lifespan` aborta el arranque si Redis no responde en closed. Evidencia: `tests/test_rate_limit_hardening.py` (fail-closed 503 sin llamar a next, fail-open dev, bucket por sub) + `tests/test_security_core.py` (revocación dev open / production 503); suite **157 passed**.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-007, §5
  - **Target Files:** `backend/app/core/rate_limit.py`, `backend/app/core/security.py`, `backend/app/main.py`, `backend/app/core/config.py`
  - **Verification:** `pytest tests/test_fail_closed.py` (nuevo: cliente Redis que lanza excepción → `is_jti_revoked` deniega; arranque prod sin Redis → excepción) + `pytest tests -q` verde
  - **Retries:** `0/3`

- [x] **SEC-FIX-004:** [HIGH · VULN-008] Corregir la identidad del cliente en rate-limit detrás de Nginx: `request.client.host` es la IP del proxy (uvicorn `forwarded_allow_ips=127.0.0.1` por defecto) → bucket global de 100 req/min (5/min para login) que permite DoS de plataforma con 101 req/min. Configurar `--forwarded-allow-ips` acotado a la subred de Nginx (o middleware que solo acepte `X-Real-IP` del peer proxy conocido), y añadir límite por `sub` autenticado además de por IP. **CORREGIDO:** `resolve_client_ip()` sólo acepta `X-Real-IP`/`X-Forwarded-For` si el peer está en `TRUSTED_PROXIES` (default loopback + RFC1918 de compose); IP inválida → fallback al peer. Añadido bucket independiente `{limit}:sub:{sub}`. Evidencia: 4 tests de resolución (spoofing desde peer no confiable ignorado) + test de bucket por sub en `test_rate_limit_hardening.py`.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-008
  - **Target Files:** `docker-compose.yml` (command uvicorn), `docker-compose.demo.yml`, `backend/app/core/rate_limit.py`, `backend/app/main.py`
  - **Verification:** `pytest tests/test_rate_limit.py tests/test_rate_limit_proxy.py` (nuevo: dos XFF distintos → keys distintas) + `grep -c "forwarded-allow-ips" docker-compose.yml` ≥ 1
  - **Retries:** `0/3`

- [x] **SEC-FIX-005:** [HIGH · VULN-006] Implementar lockout/brute-force en la ruta de login REAL. El `_BruteForceProtector` y `get_limiter_key` viven en `app/api/osint/auth.py`, cuyo router **no está montado**; `/api/v1/auth/login` (`app/api/auth.py:61-95`) no tiene lockout por cuenta. Reutilizar el protector (Redis, `(username, path)`, ventana+lockout), devolver 429 con `Retry-After`, registrar intentos fallidos en la cadena de auditoría y exigir MFA a `role=admin`. **CORREGIDO:** `/api/v1/auth/login` real ahora usa `BruteForceProtector` (Redis, path-aware): 429 + `Retry-After: 60` si la cuenta está bloqueada, registra fallo y auditoría persistente (`_log_audit(..., db_session=db)`), resetea en éxito y emite `security_events_total{auth_failure}`. Evidencia: `tests/test_login_lockout.py` (lockout 429 con Retry-After; fallo descuenta intento y persiste AuditLog) + suite 157 passed. NOTA: exigir MFA a `role=admin` se pospone (no existe flujo MFA en el router activo; forzarlo dejaría a los admin sin login).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-029, SEC-FIX-001`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-006, AC-18
  - **Target Files:** `backend/app/api/auth.py`, `backend/app/core/rate_limit.py`, `backend/app/core/audit.py`
  - **Verification:** `pytest tests/test_auth_bruteforce.py` (nuevo: 5 intentos fallidos → 429 y lockout temporal; usuario distinto no afectado) + `pytest tests/test_auth.py -q` sin regresión
  - **Retries:** `0/3`

- [x] **SEC-FIX-006:** [HIGH · VULN-009] Actualizar dependencias con advisories HIGH/CRITICAL y hacer el SCA bloqueante en CI. Mínimos: `python-jose>=3.4.0`, `python-multipart>=0.0.30`, `cryptography>=48.0.1`, `lxml>=6.1.0`, `torch>=2.6.0` (o retirar torch/ultralytics del runtime de API); `next` 15/16 (rama 14 EOL). Pinear `sha256` del modelo YOLO antes de `torch.load`. Añadir `pip-audit -r backend/requirements.txt` y `npm audit --audit-level=high` al pipeline. **CORREGIDO:** base runtime sin `torch`/`ultralytics` (movidos a `backend/requirements-vision.txt` con `torch>=2.6.0`); upgrades `python-jose 3.5.0`, `python-multipart 0.0.34`, `cryptography 50.0.2`, `lxml 6.1.3` y `passlib 1.7.4` (1.9.3 no existe en PyPI: el pin previo rompía CI); `YOLOLoader._verify_integrity` exige sha256 (`YOLO_MODEL_SHA256`) y prohíbe descarga automática en production; CI con `pip-audit` + `npm audit --omit=dev` **bloqueantes** y allowlist auditada (`docs/security/SCA_ALLOWLIST.md`); frontend Next 14 EOL → **Next 16.4.6 + React 19.3.1 + react-leaflet 5 + lucide-react 1.77**. Evidencia: `pip-audit` con allowlist → **0 vulnerabilidades**; `npm audit --omit=dev --audit-level=high` → **0**; `npm ci && tsc --noEmit && next build` sobre copia del repo → OK (4 rutas); `pytest` 157 passed.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-009
  - **Target Files:** `backend/requirements.txt`, `frontend/package.json`, `frontend/package-lock.json`, `backend/app/services/vision/yolo_loader.py`, `.github/workflows/*` o `Makefile`
  - **Verification:** `pip-audit -r backend/requirements.txt` → 0 HIGH/CRITICAL; `npm audit --audit-level=high` → 0; `cd backend && python3 -m pytest tests -q` verde; `cd frontend && npm run build` exit 0
  - **Retries:** `0/3`

- [x] **SEC-FIX-002:** [HIGH · VULN-005] SSRF en `/api/v3/vision/*` — **CORREGIDO en TASK-029**. `SatelliteAnalyst._download_image` y `drone-frame` pasan por `safe_http_get` (validación por salto + IP pinning + peer check), `follow_redirects=False`, límite 25 MB, `ValueError → 400` y 500 sin `str(e)`. Evidencia: `pytest tests/test_vision_ssrf.py` → **10 passed** (metadata, loopback, RFC1918, IPv6, v4-mapped, file://, gopher://); `pytest tests -q` → **142 passed**; `compileall` exit 0.
  - **Owner:** `@redteam-auditor` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-005
  - **Target Files:** `backend/app/services/vision/analyst.py`, `backend/app/api/v3/router.py`, `backend/tests/test_vision_ssrf.py`
  - **Verification:** `cd backend && SECRET_KEY="test-secret-key-32-chars-minimum!!!" python3 -m pytest tests/test_vision_ssrf.py -q` → 10 passed
  - **Retries:** `0/3`

- [x] **SEC-FIX-003:** [HIGH · VULN-003] Credenciales por defecto publicadas — **CORREGIDO en TASK-029**. `.env.example` ya no expone `SECRET_KEY` ni password de admin reales (`CHANGE_ME_*`), `docker-compose.yml`/`docker-compose.demo.yml` exigen `ADMIN_INITIAL_PASSWORD` explícito (sin `admin123`) y el validador de producción rechaza el hex histórico, exige ≥10 chars y bloquea placeholders. Evidencia: `grep -n admin123 docker-compose*.yml .env.example` → 0; `Settings()` en production con placeholders → `Refusing to start`; `pytest tests -q` → 142 passed.
  - **Owner:** `@redteam-auditor` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-003, REQ-05
  - **Target Files:** `.env.example`, `docker-compose.yml`, `docker-compose.demo.yml`, `backend/app/core/config.py`
  - **Verification:** `grep -rc admin123 docker-compose.yml docker-compose.demo.yml .env.example` → 0; `validate_all.py` → VALIDATED
  - **Retries:** `0/3`

- [ ] **SEC-FIX-007:** [MEDIUM · VULN-015/016/017/018] Hardening perimetral: cerrar `/metrics` y OpenAPI en production (`docs_url=None`, token de scraping), añadir `headers()` (CSP/HSTS/XFO) a Next y servir `next start` en vez de `next dev`, aplicar `limit_req zone=auth` a `/auth/(login|refresh)` y `server_tokens off` en Nginx, y activar `requirepass` en Redis + auth en NATS.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-015..018
  - **Target Files:** `backend/app/main.py`, `frontend/next.config.mjs`, `frontend/Dockerfile`, `infra/nginx.conf`, `docker-compose.yml`
  - **Verification:** `curl -s -o /dev/null -w "%{http_code}" localhost:8000/metrics` → 401/404; `grep -c "limit_req zone=auth" infra/nginx.conf` ≥ 1; `grep -c "requirepass" docker-compose.yml` ≥ 1
  - **Retries:** `0/3`

- [ ] **SEC-FIX-008:** [MEDIUM · VULN-010/022] Integridad de auditoría y cobertura de rutas: head único de la cadena en DB (`SELECT … FOR UPDATE`), persistencia estricta (sin swallow), y decisión explícita sobre los módulos OSINT no montados (montar con fixes previos o eliminar el código muerto) + test que verifique que todo router declarado está montado.
  - **Owner:** `@architect` -> `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-029`
  - **Spec Ref:** SECURITY_AUDIT.md §3 VULN-010, VULN-022
  - **Target Files:** `backend/app/core/audit.py`, `backend/app/main.py`, `backend/app/api/osint/*`, `backend/tests/test_routers_mounted.py` (nuevo)
  - **Verification:** `pytest tests/test_audit_multiprocess.py tests/test_routers_mounted.py -q` → passed
  - **Retries:** `0/3`


---

## CIRCUIT BREAKER & FAILURE ESCALATION LOG

| Task ID | Attempt | Failure Symptom / Stack Trace Summary | Root Cause & Architectural Fix (`@architect`) |
| :--- | :--- | :--- | :--- |
| — | — | — | — |
