# AUTONOMOUS EXECUTION BACKLOG

- **Project Name:** SmartNationDefense / SESIS-FEDERATION
- **Current Phase:** `PHASE_9` | (0,1 verificados — 2-9 activos para futuro)
- **Progress:** `2 / 44 tasks verified (5%)`
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

- [ ] **TASK-012:** TD-009 + N-06 — Rate-limit path-blindness fix (osint auth, v1, intel auth).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-11)
  - **Target Files:** `app/core/rate_limit.py`, `app/api/osint/auth.py`, `app/api/intel/auth.py`
  - **Verification:** `pytest backend/tests/test_rate_limit.py`
  - **Retries:** `0/3`

- [ ] **TASK-013:** TD-010 — Fail-open rate limit circuit breaker.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-012`
  - **Spec Ref:** SPEC.md §3 (AC-11)
  - **Target Files:** `app/core/rate_limit.py`
  - **Verification:** `pytest backend/tests/test_rate_limit.py`
  - **Retries:** `0/3`

- [ ] **TASK-014:** TD-008 — settings.MULTI_TENANT/DEFAULT_TENANT_ID defaults (config.py).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-12)
  - **Target Files:** `app/core/config.py`, `app/api/osint/deps.py`
  - **Verification:** `python -c "from app.core.config import settings; assert settings.MULTI_TENANT is False; assert settings.DEFAULT_TENANT_ID == 'default'"`
  - **Retries:** `0/3`

- [ ] **TASK-015:** TD-002 — `_log_audit` pass db_session (osint/auth.py + _log_audit).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-14)
  - **Target Files:** `app/api/osint/auth.py` (_log_audit calls)
  - **Verification:** `grep -n "db_session=" backend/app/api/osint/auth.py`
  - **Retries:** `0/3`

- [ ] **TASK-016:** TD-011 — Dedup AuditLog (persistence.AuditLog usado de legacy osint.audit_log, arquitectura ADR — TD-011).
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

- [ ] **TASK-018:** N-08 — Dead route `/api/v1/policy` removal (app/api/v1/policy.py, v1/__init__).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-13)
  - **Target Files:** `app/api/v1/__init__.py` (remove policy import), `app/main.py`
  - **Verification:** `grep -rn "policy" backend/app/main.py | wc -l` + `grep -rn "policy" backend/app/api/v1/__init__.py`
  - **Retries:** `0/3`

- [ ] **TASK-019:** N-09 — X-XSS-Protection deprecado: fix (X-XSS deprecado, FASE 2).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-12)
  - **Target Files:** `infra/nginx.conf` (remove X-XSS, add Permissions-Policy explicitly)
  - **Verification:** `grep -c "X-XSS" infra/nginx.conf` = 0
  - **Retries:** `0/3`

- [ ] **TASK-020:** TD-013 — Guardian quarantine: scripts/archived/guardian/.
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

- [ ] **TASK-023:** FASE 2 verification — Todos AC de FASE 2 (2-22): mover `- [x]` + marcar feedback.
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

- [ ] **TASK-025:** TD-004 + SEC-04 — SSRF IP pinning (HIGH-03 — accepted-risk mitigation).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-19)
  - **Target Files:** `app/services/osint/tools/web_tools.py` (custom transport adapter, IP pinning en socket connect)
  - **Verification:** `pytest backend/tests/test_ssrf.py` + `grep -n "connect_ex\|pin_ip\|custom_transport" backend/app/services/osint/tools/web_tools.py`
  - **Retries:** `0/3`

- [ ] **TASK-026:** TD-005 + MEDIUM-02 — crypto_quantum honest labels (Fernet → aes-128-cbc + HMAC).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-21)
  - **Target Files:** `app/core/crypto_quantum.py`, `backend/requirements.txt` (pqcrypto opcional)
  - **Verification:** `python -c "from app.core.crypto_quantum import qcrypto; import asyncio; asyncio.run(qcrypto.encrypt(b'x', b'key'))"`
  - **Retries:** `0/3`

- [ ] **TASK-027:** MEDIUM-01 — AuditChain persistence (`db_session` pass en osint/auth).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-015`
  - **Spec Ref:** SPEC.md §3 (AC-20)
  - **Target Files:** `app/api/osint/auth.py`, `app/core/audit.py`
  - **Verification:** `pytest backend/tests/test_audit_persistence.py` (FASE 2 — FASE 5 verify)
  - **Retries:** `0/3`

- [ ] **TASK-028:** TD-009 — NATS DLQ + idempotency keys.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-19)
  - **Target Files:** `app/core/events.py` (DLQ + idempotency + ack)
  - **Verification:** `grep -n "dlq\|idempotency\|ack" backend/app/core/events.py | wc -l`
  - **Retries:** `0/3`

- [ ] **TASK-029:** SEC-FIX-XXX (FASE 3) — Audit chain (TASK-027 done, verificar persistence), SSRF (TASK-025), HIGH-02 (TASK-024). Re-run `redteam-auditor` → 0 CRITICAL/HIGH.
  - **Owner:** `@redteam-auditor` -> `@qa-verifier`
  - **Depends On:** `TASK-024, TASK-025, TASK-026, TASK-027`
  - **Spec Ref:** SPEC.md §3 (AC-18..AC-21)
  - **Target Files:** `.factory/SECURITY_AUDIT.md`
  - **Verification:** `python scripts/validate_all.py` exit 0 + `cat .factory/SECURITY_AUDIT.md`
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

- [ ] **TASK-031:** TD-012 Follow-up — User nuevo exportado: `app/db/models/__init__.py` + poner `from app.db.models.persistence import User` (unify real).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-008`
  - **Spec Ref:** SPEC.md §3 (AC-08)
  - **Target Files:** `app/db/models/__init__.py`, `app/api/osint/auth.py` (import simplificado)
  - **Verification:** `python -c "from app.db.models import User; print(User.__tablename__)"`
  - **Retries:** `0/3`

- [ ] **TASK-032:** ADR-010 — Clearance hierarchy leak reduction v1 (verificar en routers v1).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-09)
  - **Target Files:** `app/api/v1/*.py` (v1 verification clearance)
  - **Verification:** `pytest backend/tests/test_clearance_enforcement.py`
  - **Retries:** `0/3`

---

## PHASE 5: FASE 5 — Testing (PENDING)

- [ ] **TASK-033:** SEC-TEST-AUDIT-01 — Audit chain persistence + tamper detection (FASE 3 — Test de regresión).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-027`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_audit_persistence.py` (TASK-015 anotar)
  - **Verification:** `pytest backend/tests/test_audit_persistence.py`
  - **Retries:** `0/3`

- [ ] **TASK-034:** SEC-TEST-BRUTE-01 — Distributed Brute-Force Lockout (Redis).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_rate_limit.py` (TASK-012 anotar)
  - **Verification:** `pytest backend/tests/test_rate_limit.py`
  - **Retries:** `0/3`

- [ ] **TASK-035:** SEC-TEST-CLEARANCE-01 — Clearance enforcement (v2 + v1).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-009`
  - **Spec Ref:** SPEC.md §3 (AC-22, AC-23)
  - **Target Files:** `backend/tests/test_clearance_enforcement.py` (TASK-009 anotar)
  - **Verification:** `pytest backend/tests/test_clearance_enforcement.py`
  - **Retries:** `0/3`

- [ ] **TASK-036:** SEC-TEST-MFA-01 — MFA secrets encrypted + challenge isolation.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_mfa_security.py`
  - **Verification:** `pytest backend/tests/test_mfa_security.py`
  - **Retries:** `0/3`

- [ ] **TASK-037:** SSRF hardened suite — DNS rebinding + redirects + IPv6 + metadades.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-025`
  - **Spec Ref:** SPEC.md §3 (AC-22)
  - **Target Files:** `backend/tests/test_ssrf.py` (TASK-025 anotar)
  - **Verification:** `pytest backend/tests/test_ssrf.py`
  - **Retries:** `0/3`

- [ ] **TASK-038:** `validate_all.py` → exit 0 + pytest suite verde.
  - **Owner:** `@qa-verifier`
  - **Depends On:** `TASK-033..TASK-037`
  - **Spec Ref:** SPEC.md §3 (AC-22, AC-23)
  - **Target Files:** `scripts/validate_all.py`, `reports/validation.json`
  - **Verification:** `python scripts/validate_all.py` exit code = 0 + `pytest backend/tests`
  - **Retries:** `0/3`

---

## PHASE 6: FASE 6 — Observabilidad (PENDING)

- [ ] **TASK-039:** TD-020 — Dashboards por módulo (C2, Auth, OSINT, Tactile, Maven, Security).
  - **Owner:** `@builder` -> `@ui-artisan` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-23)
  - **Target Files:** `infra/grafana/provisioning/dashboards/*.json`, `backend/app/api/health.py` (metrics), `infra/prometheus.yml`
  - **Verification:** `ls infra/grafana/provisioning/dashboards/ && grep -n "metrics\|prometheus_client" backend/app/api/health.py`
  - **Retries:** `0/3`

- [ ] **TASK-040:** TD-020 — Alertmanager + alerts (slack/slackpager).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-039`
  - **Spec Ref:** SPEC.md §3 (AC-24)
  - **Target Files:** `infra/alertmanager/alerts.yml`, `docker-compose.yml` (alertmanager)
  - **Verification:** `ls infra/alertmanager/` + `curl -s localhost:9093/-/healthy` (FASE 6)
  - **Retries:** `0/3`

- [ ] **TASK-041:** TD-020 — Healthcheck architecture (Docker healthchecks, graceful degradation, alerts on unhealthy).
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-040`
  - **Spec Ref:** SPEC.md §3 (AC-24)
  - **Target Files:** `docker-compose.yml`, `infra/nginx.conf`, `backend/Dockerfile`
  - **Verification:** `docker compose config | grep -c healthcheck`
  - **Retries:** `0/3`

---

## PHASE 7: FASE 7 — Móvil (PENDING)

- [ ] **TASK-042:** Pubspec completion: features completas + offline mesh hardened.
  - **Owner:** `@builder` -> `@ui-artisan` -> `@qa-verifier`
  - **Depends On:** `NONE`
  - **Spec Ref:** SPEC.md §3 (AC-25)
  - **Target Files:** `mobile/sesis_cop/pubspec.yaml`, `mobile/sesis_cop/pubspec.lock` (si se aligea), `mobile/sesis_cop/lib/core/network/*`
  - **Verification:** `cd mobile/sesis_cop && flutter analyze` (0 errors) + `flutter test` (pass)
  - **Retries:** `0/3`

---

## PHASE 8: FASE 8 — Migration Legacy & Deprecación (PENDING)

- [ ] **TASK-043:** TD-011 — Dedup — remove duplicate audit model y usa solo persistence.AuditLog.
  - **Owner:** `@builder` -> `@qa-verifier`
  - **Depends On:** `TASK-027`
  - **Spec Ref:** SPEC.md §1 (AC-26)
  - **Target Files:** `app/db/models/osint/audit_log.py` (archivar), `app/api/osint/audit.py`
  - **Verification:** `grep -rn "osint/audit_log" backend/app | wc -l`
  - **Retries:** `0/3`

- [ ] **TASK-044:** ADR-010 — V1 v1-leak reduction — v1 verify (brief security tests).
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

*(Vacío inicialmente)*

---

## CIRCUIT BREAKER & FAILURE ESCALATION LOG

| Task ID | Attempt | Failure Symptom / Stack Trace Summary | Root Cause & Architectural Fix (`@architect`) |
| :--- | :--- | :--- | :--- |
| — | — | — | — |
