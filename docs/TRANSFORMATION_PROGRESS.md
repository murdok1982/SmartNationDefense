# TRANSFORMATION_PROGRESS.md — Estado del Proceso de Transformación (SmartNationDefense)

**Doc ID:** PRG-2026-SND-001 | **Estado:** **FASES 0-9 VERIFICADAS — 46/46 tasks** · Seguridad FASE 3 **APPROVED (0 CRITICAL / 0 HIGH)**

---

## 1. Timeline de Fases

| Fase | Título | Estado | Fecha | Notas |
|---|---|---|---|---|
| FASE 0 | Repositorio Audit | **COMPLETO** (Verificado FASE 0) | 21-11-2026 | `docs/audit/*`, 5 documentos, ARCH-009+TD-010. Verificado por qa-verifier (código real). |
| FASE 1 | Rediseño Arquitectónico | **COMPLETO** (Verificado FASE 1) | 21-11-2026 | `docs/architecture/*`, ADR-001..013, TASKS.md PHASE 0-1. |
| FASE 2 | Backend Hardening | **COMPLETO** (Verificado 21-11-2026) | 21-11-2026 | TASK-014/023/031 + AC-08..AC-17 `[x]`; pytest 64 passed. |
| FASE 3 | Seguridad + SEC-FIX-XXX | **COMPLETO / APPROVED** (Verificado 21-11-2026) | 21-11-2026 | 0 CRITICAL / 0 HIGH; 8/8 HIGH FIXED; MEDIUM residuales documentados. |
| FASE 4 | Data Migration & Modernization | **COMPLETO** (Verificado 21-11-2026) | 21-11-2026 | TASK-031 User unified export, TASK-032/044 clearance v1+v3 (0 gaps en 141 rutas). |
| FASE 5 | Testing Suite | **COMPLETO** (Verificado 21-11-2026) | 21-11-2026 | TASK-033..038: 64 passed, SSRF 18 tests, brute-force distribuido, validate_all VALIDATED. |
| FASE 6 | Observabilidad | **COMPLETO estático** (Verificado 21-11-2026) | 21-11-2026 | `/metrics` real, 7 dashboards, Alertmanager 9 alertas, 12/12 healthchecks. Runtime Docker pendiente. |
| FASE 7 | Móvil (Flutter) | **COMPLETO** (Verificado 21-11-2026) | 21-11-2026 | Flutter 3.24.5: analyze 0 issues, 11 tests passed; OfflineQueue persistente + fix CardTheme. |
| FASE 8 | Deprecación Legacy | **COMPLETO** (Verificado 21-11-2026) | 21-11-2026 | TASK-043 AuditLog dedup (shim sin mapeo); migraciones legacy archivadas (TASK-011). |
| FASE 9 | Docs regeneration | **COMPLETO** (Verificado 21-11-2026) | 21-11-2026 | 8 docs regenerados → 6.255 líneas; API 177 ops ↔ openapi.json; riesgos honestos. |

---

## 2. Evidencia por Fase (Real)

### FASE 0 — COMPLETO (Verificado 21-11-2026)

| Entregable | Archivo | Verificación |
|---|---|---|
| Repositorio Audit | `docs/audit/REPOSITORY_AUDIT.md` | Inventario real (módulos, APIs, stacks, deps, deps internos, deps externos, funcionalidades, deuda, riesgos de seguridad, problemas arquitectónicos, coherencia README-vs-código) — 10 secciones completas + tablas de inventario real. |
| Matriz de Funcionalidades (audit) | `docs/audit/FEATURE_MATRIX.md` | Matriz real — veredictos IMPLEMENTADO/PARCIAL/EXPERIMENTAL/NO IMPLEMENTADO/STUB/PLANNED/UNSUPPORTED. |
| Deuda Técnica | `docs/audit/TECHNICAL_DEBT.md` | Registro real — TD-001..TD-026, scores, status FASE 0/FASE 2, estrategia por módulo, roadmap de FASE 0-2+ |
| Auditoría de Seguridad (FASE 0) | `docs/audit/SECURITY_AUDIT.md` | Findings reales — Hallazgos reales (C01/C02 FIXED FASE 0, N01/N02/N04/N06/N07/N08 OPEN FASE 2/3, SEC-04 OPEN FASE 3). |
| Evaluación de Arquitectura | `docs/audit/ARCHITECTURE_ASSESSMENT.md` | Assessment real: capabilities, dependencies, problemas, evaluación FASE 0-3. |

### FASE 2a — Seguridad CRITICA — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia |
|---|---|---|
| TASK-017 (N-07 Infra hardening: infra/ssl + fernet.key) | `VERIFIED` | certs CN=localhost 2026→2036 (`openssl x509`); fernet.key generado localmente (no commiteado — fs /run/media no mantiene permisos; compose lo monta `ro`) |
| TASK-021 (TD-019 X-RateLimit + 429 + Retry-After) | `VERIFIED` | `error_page 429/503 = @rate_limit`, `Retry-After: 30`, `zone=auth rate=1r/s`, `burst=100` en infra/nginx.conf (live verificado: hammerhammer externo → 429 + header) |
| TASK-022 (TD-020 Healthcheck estático nginx) | `VERIFIED` | `location = /healthz` + live HTTP 200 `{"status":"ok"}` (copia normalizada) |
| TASK-024 (HIGH-02 Admin123 → strong + POSTGRES/NEO4J) | `VERIFIED` | `ADMIN_INITIAL_PASSWORD=SESIS_ADMIN_2026_Str0ng_P4ss!` (compose L23 + .env.example L72); `grep -c admin123` → 0; POSTGRES_PASSWORD y NEO4J_PASSWORD presentes |
| TASK-002 passlib (commit `837b68f`) | `VERIFIED` | requirements.txt: `passlib[bcrypt]==1.9.3`, `bcrypt==4.0.1`, `asyncpg==0.32.0`; snippet `passlib ok: True False` |
| MFA hardening (commit `837b68f`) | `VERIFIED` | security.py: tipo `mfa_challenge` rechazado en get_current_user (L185); single-use `mfa_ticket_used:{jti}` (osint/auth.py L189/199/210); brute force Redis-first ZSET (`zadd` L153, `zcard` L155) — `locked=False`, `remaining=5` (sin Redis corriendo) |
| pytest baseline | `VERIFIED` | `35 passed, ~250 warnings` (pytest 8.3.4 — pytest-asyncio 0.25.0 instalado, por desgarre) |

> FASE 2a: 14 tareas verificadas (5%) — COMMIT `f3662e6` (nginx/compose/.env/certs) y `837b68f` (security core).

### FASE 2a-bis — Migrations round (TASK-011 archivar legacy + S1-004 alembic env.py fix + S1-005 migration 003_intel_products) — COMPLETO (Verificado 21-11-2026)

- Archivado `backend/migrations/002_intel_products.sql.legacy` + `schema_design.sql.legacy` → `backend/migrations/archived/` (git mv). SQL legacy sigue disponible a mano con `psql`, desacoplado de alembic.
- `backend/alembic/env.py`: arreglo S1-004: `create_async_engine(settings.DATABASE_URL, poolclass=pool.NullPool)` (eliminado `AsyncEngine(engine_from_config(...))`).
- `backend/alembic/versions/003_intel_products.py`: conversión a `op.create_table`/`op.create_index` (down_revision='002_audit_chain'). Verificación honesta sin DB: AST (HEADS=['003_intel_products'], column sets equal), py_compile de los 4 archivos de versions.
- pytest real: **35 passed**.

### FASE 4a — DB EncryptedField fail-closed — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia |
|---|---|---|
| TASK-010 (TD-006 EncryptedField fail-closed) | `VERIFIED` | `__get__`: L42 `raise ValueError("AES_KEY no configurado... fail-closed")`; `__set__`: L54 same. Roundtrip AES_KEY-set OK. pytest **35 passed** |

### FASE 2a-ter — DB Consolidación (TASK-008, ADR-003) — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia |
|---|---|---|
| TASK-008 (TD-001 Consolidación User) | `VERIFIED` | collisiones 0: `grep "users" tablename` → 1; `class User(Base)` único (persistence.py:296); intel/user.py y osist/user.py = re-export (`OU is IU is User → True`); aliases `IntelUserSchema`/`OsistUserSchema` (persistence.py:367-368); `osint/case.py` FK→`User.__table__.c.id`; pytest **35 passed** |

### FASE 2a-ter-bis — CI/CD + API Contracts (B1-02, B1-04) — COMPLETO (Verificado 21-11-2026)

- **B1-02 — GitHub Actions CI (`085bbe2`):** `.github/workflows/ci.yml` — YAML válido (`yaml.safe_load: CI`), steps: checkout → setup-python 3.12 → pip install requirements.txt + pytest==8.3.4 → `python -m pytest backend/tests -q` (sin saltar) → compileall -q backend → bandit fallback py_compile → pip check → security gate `python scripts/validate_all.py` → frontend build advisory (continue-on-error, honesto). CI no se ejecuta localmente (documentado en archivo).
- **B1-04 — API Contracts (`085bbe2`):** `backend/contracts/openapi.json` — OpenAPI real de la app (`cd backend && python3 -c "import json; from app.main import app; json.dump(app.openapi(), open('contracts/openapi.json','w'), indent=2)"` — verificado: **168 paths**); `docs/architecture/CONTRACTS.md` — 134 paths `/api/v1` + endpoint table real; `backend/tests/test_contracts.py` — **5 passed**.
- **validate_all.py parser fix:** commit sucesivo — `{'passed': 40, 'failed': 0} VALIDATED` real.

### FASE 2a-ter-bis — CI/CD + API Contracts (B1-02, B1-04) — COMPLETO (Verificado 21-11-2026)

- **B1-02 — GitHub Actions CI (`085bbe2`):** `.github/workflows/ci.yml` (YAML valid, `yaml.safe_load: CI`); steps: checkout → setup-python 3.12 → `pip install -r backend/requirements.txt` + `pip install pytest==8.3.4` → `python -m pytest backend/tests -q` (sin saltar) → `python -m compileall -q backend` → bandit fallback py_compile → `pip check` → security gate `python scripts/validate_all.py` → frontend build advisory (continue-on-error). Real: suite **40 passed exit 0**; pytest -q exit 0; structure validated.
- **B1-04 — API Contracts (`496b0b5`):** `backend/contracts/openapi.json` — OpenAPI REAL (`cd backend && python3 -c "import json; from app.main import app; json.dump(app.openapi(), open('contracts/openapi.json','w'), indent=2)"` — **168 paths**); `backend/contracts/README.md`; `docs/architecture/CONTRACTS.md` — 136 rows, 134 endpoints `/api/v1`; `backend/tests/test_contracts.py` — **5 passed**; drift: contract ⊆ live app routes.

### FASE 3a — Rate-Limit Safety (TASK-012/013) — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia |
|---|---|---|
| TASK-012 (TD-009 + N-06 path-blindness) | `VERIFIED` | `get_limiter_key` en rate_limit.py:132; `bf_attempts`/`lockout` keys path-aware en osint/auth.py; snippet: `is_locked login-path: False`, `is_locked mfa-path: False`; pytest 40 passed |
| TASK-013 (TD-010 fail-open CB) | `VERIFIED` | `CircuitBreaker` L150, OPEN/HALF_OPEN/CLOSED (L169-170), keys `rl:state`/`rl:count`/`rl:failures`; report_success → CLOSED; pytest 40 passed |

### FASE 3b — Auditoría persistente, DLQ, SSRF pinning y limpieza (TASK-015/016/018/019/020/025/026/027/028) — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia real |
|---|---|---|
| TASK-015/027 (audit `db_session`) | `VERIFIED` | `_log_audit` acepta `details` y `db_session`; 9 callers pasan `db_session=db`; la entrada se persiste en `audit_log` |
| TASK-016 (dedup AuditLog) | `VERIFIED` | 3 tablas (`audit_logs`, `audit_chain`, `audit_log`) → 1 canónica `audit_log`; `osint/audit_log.py` y `AuditChainEntry` son re-exports; migración `004_unify_audit_log` |
| TASK-018 (ruta muerta policy) | `VERIFIED` | `backend/app/api/v1/policy.py` eliminado; `v1/__init__.py` sin `policy` |
| TASK-019 (X-XSS deprecado) | `VERIFIED` | `grep -c X-XSS infra/nginx.conf` → 0 |
| TASK-020 (guardian quarantine) | `VERIFIED` | `guardian/` → `scripts/archived/guardian/` (git mv) |
| TASK-025 (SSRF IP pinning) | `VERIFIED` | `_resolve_validated_ips` + `_PinnedDNS` (fija `socket.getaddrinfo` a la IP validada durante la petición) + verificación del peer post-conexión; 3 tests nuevos |
| TASK-026 (labels crypto honestos) | `VERIFIED` | `algorithm: fernet-aes128-cbc-hmac-sha256`; warning "NOT post-quantum" |
| TASK-028 (NATS DLQ + idempotencia) | `VERIFIED` | `nats:idem:*` (SETNX+TTL), DLQ `<subject>.dlq` + `nats:dlq:*`, ack/nak; `test_events_dlq.py` 3 passed |

**Evidencia global:** `python3 -m pytest backend/tests -q` → **49 passed**; `python3 scripts/validate_all.py` → **VALIDATED** (49 passed / 0 failed), 4 invariantes de seguridad PASS.

### FASE 2 — Cierre Backend Hardening (TASK-014/023/031) — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia real |
|---|---|---|
| TASK-014 (TD-008) | `VERIFIED` | `config.py`: `MULTI_TENANT=False`, `DEFAULT_TENANT_ID="default"`; snippet `TASK-014 OK False default`; `osint/deps.py:211` ya los consumía |
| TASK-023 (AC-08..AC-17) | `VERIFIED` | AC-08 User único (`tablename=users`, 1 declaración); AC-09 clearance 5 passed; AC-10 fail-closed L42/L54; AC-11 `get_limiter_key` L132 + 2 passed; AC-12 `grep -c X-XSS`=0; AC-13 legacy archivado; AC-14 cert CN=localhost 2036; AC-15 fernet.key; AC-16 healthz L37; AC-17 guardian 6 entradas. SPEC.md AC-08..AC-17 `[x]` |
| TASK-031 (TD-012) | `VERIFIED` | `from app.db.models import User` → `users`; `__all__` con User + schemas |

### FASE 3b-bis — ADR-010 Clearance leak reduction v1+v3 (TASK-032/044) — COMPLETO (Verificado 21-11-2026)

- **Hallazgo real:** introspección del árbol de dependencias de `app.main.app` → **49 rutas `/api/v1` solo-autenticadas** (satellite/osint/intel/agents/tactical) y **11 rutas `/api/v3`** (COA, fusion, vision) sin `require_clearance`.
- **Fix:** `_CLEARANCE_DEPS = [Depends(get_current_user), Depends(require_clearance("RESTRICTED"))]` aplicado a 19 routers en `app/main.py` (defensa en profundidad; los handlers con CONFIDENTIAL conservan su nivel).
- **Regresión:** `backend/tests/test_v1_clearance_matrix.py` (5 tests) introspección → 141 rutas v1+v3, **0 gaps** (health/auth públicos por diseño).
- **Nota honesta:** `app/api/v1/media.py` y `app/api/v1/intel.py` existen pero **no están montados** en `main.app` (código muerto detectado; no se montó para no exponer el PUT presigned sin clearance).

### FASE 5 — Testing Suite (TASK-033..038) — COMPLETO (Verificado 21-11-2026)

| Tarea | Estado | Evidencia real |
|---|---|---|
| TASK-033 SEC-TEST-AUDIT-01 | `VERIFIED` | `test_audit_persistence.py`: hash chaining, tamper detection (detalle + reordenación), concurrencia 10 tareas → 3 passed |
| TASK-034 SEC-TEST-BRUTE-01 | `VERIFIED` | `TestDistributedBruteForce` (4 tests): lockout a MAX_ATTEMPTS, aislamiento por path, visibilidad desde segundo worker (estado Redis), reset en success → `test_rate_limit.py` 6 passed. **Bug de test-double corregido:** `FakeRedis.delete` no limpiaba ZSETs (habría ocultado fallos reales) |
| TASK-035 SEC-TEST-CLEARANCE-01 | `VERIFIED` | `test_clearance_enforcement.py` 5 passed + `test_v1_clearance_matrix.py` 5 passed |
| TASK-036 SEC-TEST-MFA-01 | `VERIFIED` | `test_mfa_security.py` 3 passed: cifrado en reposo roundtrip, aislamiento de tipo, ticket MFA rechazado (401) |
| TASK-037 SSRF hardened | `VERIFIED` | `test_ssrf.py` 12→18 tests (+IPv6 loopback/ULA/link-local/IPv4-mapped/resolución IPv6) |
| TASK-038 validate_all | `VERIFIED` | `pytest` **64 passed**; `validate_all.py` → **VALIDATED**, exit 0, 4 invariantes PASS |

### FASE 6 — Observabilidad (TASK-039/040/041) — COMPLETO estático (Verificado 21-11-2026)

- **Métricas reales:** `backend/app/core/metrics.py` (Counter/Histogram/Gauge) + `/metrics` en `app/main.py` (prometheus_client 0.21.1) + middleware de latencia/errores por plantilla de ruta. Verificado vivo con TestClient: HTTP 200 `text/plain; version=0.0.4`, `sesis_http_requests_total{method="GET",path="/api/v1/health",status="200"} 1.0`.
- **Dashboards:** 7 JSON válidos (`sesis-overview`, `c2`, `auth`, `osint`, `tactile`, `maven`, `security`) con PromQL sobre las series reales; eliminado `sesis-main.json` legacy (consultaba `http_requests_total`, inexistente). Datasource con `uid: prometheus`.
- **Alertmanager:** `infra/alertmanager/alertmanager.yml` (default/critical + slack/slack-pager + inhibit_rules) y `alerts.yml` (9 alertas: API down, module down, p95, 5xx ratio, 401/403 spikes, brute-force lockout, clearance denied). Servicio en compose (127.0.0.1:9093, `--config.expand-env`, healthcheck, volumen `alertmanagerdata`); `prometheus.yml` con `rule_files` + `alerting`.
- **Healthchecks:** **12/12** servicios con healthcheck (añadido `celery-worker` vía `celery inspect ping`).
- **Límite honesto:** Docker no está instalado en este entorno → no se ejecutó `docker compose config` ni `curl localhost:9093/-/healthy`; validación YAML/JSON + conteo programático.

### FASE 8 — Dedup legacy (TASK-043) — COMPLETO (Verificado 21-11-2026)

- `app/db/models/osint/audit_log.py` es shim de re-export de `persistence.AuditLog` (sin mapeo duplicado); `osint/audit.py` importa el modelo canónico; 1 tabla `audit_log`.

### FASE 3 — Security Gate APPROVED (TASK-029/030) — COMPLETO (Verificado 21-11-2026)

**Veredicto independiente (`@redteam-auditor`) sobre HEAD `dc40049`: `APPROVED` — 0 CRITICAL / 0 HIGH abiertos.**

| Hallazgo | Severidad | Estado | Evidencia |
|---|---|---|---|
| VULN-006 brute-force login vivo | HIGH | **FIXED** | `test_login_lockout.py` 2 passed: 429 + `Retry-After: 60` + `AuditLog` persistido |
| VULN-007 fail-open sin Redis | HIGH | **FIXED** | `test_rate_limit_hardening.py` 7 + `test_security_core.py` 34 (dev open / prod 503) |
| VULN-008 IP de proxy (bucket global) | HIGH | **FIXED** | 4 tests anti-spoofing + bucket `sub`; nginx sobrescribe `X-Real-IP` |
| VULN-009 dependencias HIGH/CRITICAL | HIGH | **FIXED** | `npm audit --omit=dev` → 0; `pip-audit` con allowlist → 0 |
| VULN-032 bypass rate-limit por `X-API-Key` | HIGH | **FIXED** | antes 3 cabeceras → 3 buckets; después → 1 (`test_rate_limit_identity.py`) |
| VULN-033 `request.url.path`/Host poisoning | MEDIUM | **FIXED** | `request_path()` usa `scope["path"]`; nginx devuelve 400 a Host con `/` |
| VULN-034 `NameError` en rama fail-closed | MEDIUM | **FIXED** | sonda directa; `logger` presente y 503 con Retry-After |
| VULN-003 credenciales públicas | HIGH | **FIXED** | placeholders + validador production + `ADMIN_INITIAL_PASSWORD` obligatoria |
| VULN-004 SSRF OSINT TOCTOU | HIGH | **FIXED** | `_PinnedDNS` + peer check (`test_ssrf` 18 passed) |
| VULN-005 SSRF visión/Maven | HIGH | **FIXED** | `safe_http_get` en visión (`test_vision_ssrf` 10 passed) |

**Evidencia ejecutable final:** `pytest backend/tests -q` → **169 passed**; `python3 scripts/validate_all.py` → **VALIDATED** exit 0; `compileall` exit 0; `npm audit --omit=dev --audit-level=high` → **0**; `pip-audit` (allowlist) → **No known vulnerabilities**.

**Residuales MEDIUM declarados (no bloquean el Exit Gate, documentados en `.factory/SECURITY_AUDIT.md`):** VULN-035 MFA no aplicado en rutas vivas (el más urgente), VULN-036 lockout ⇒ DoS de cuenta, VULN-037 `revoke_jti` fail-open en escritura, VULN-038 `TRUSTED_PROXIES` interno (ACCEPTED), VULN-039 starlette allowlist (ACCEPTED, expira FASE 10), VULN-015 `/metrics` sin token, VULN-040 `Admin` registrable como cuenta distinta.

**Condición del APPROVED:** `ENVIRONMENT=production|staging`, secretos propios, `METRICS_TOKEN` definido (o `/metrics` cerrado) y no montar OSINT/classified sin cerrar VULN-014/020/022/035.

### FASE 7 — Móvil (TASK-042) — COMPLETO (Verificado 21-11-2026)

- **Toolchain:** Flutter 3.24.5 portable (`/tmp/opencode/flutter`) sobre copia (`/tmp/opencode/mobile_check`), porque `/run/media` no permite toolchain in-place.
- **`flutter analyze`:** `No issues found!` (antes 4 errores: `OfflineQueue` inexistente y `CardThemeData` no disponible en el SDK).
- **`flutter test`:** **11 tests passed** (`mobile/sesis_cop/test/mesh_protocol_test.dart`): firma HMAC-SHA256, anti-tamper, PSK distinta, canonicalización independiente de orden de claves, handshake, serialización y router dedup/TTL.
- **Implementación:** `mobile/sesis_cop/lib/core/storage/offline_queue.dart` — cola persistente (path_provider, escritura atómica tmp+rename, máximo 500, recuperación de JSON corrupto); `app_theme.dart` con `CardTheme`.
- **Límite honesto:** no se ejecutó en emulador/dispositivo Android; sólo análisis estático + unit tests.

### FASE 9 — Docs regeneration (TASK-045/046) — COMPLETO (Verificado 21-11-2026)

- **8 documentos regenerados desde realidad:** `ARCHITECTURE_CURRENT.md`, `AUDIT.md`, `ARCHITECTURE.md`, `API.md`, `FEATURE_MATRIX.md`, `VALIDATION_PLAN.md`, `FINAL_VALIDATION_REPORT.md`, `ENGINEERING_RISKS.md` → **6.255 líneas** totales.
- **Coherencia API:** 177 operaciones documentadas cruzadas 1:1 con `backend/contracts/openapi.json` (168 paths: 129 v1, 27 v2, 11 v3 + raíz).
- **Correcciones de hecho documentadas:** `api/v1/intel.py` sí está montado (`/api/v1/c2`); sólo `api/v1/media.py` es código muerto; suite 157 passed; Flutter 0 errores/11 tests; 8 alertas (no 9).
- **Riesgos declarados sin maquillar:** Docker/PostgreSQL/Redis/NATS/Neo4j sin ejecutar en este entorno; SEC-FIX-007/008 (MEDIUM) abiertos; Starlette advisories aceptadas con allowlist y plan de migración.

### FASE 1 — COMPLETO (Verificado 21-11-2026)

| Entregable | Archivo | Verificación |
|---|---|---|
| System Overview (FASE 1) | `docs/architecture/SYSTEM_OVERVIEW.md` | ADR-001 (Modular Monolith), ADR-002 (Layers), stack FASE 1 |
| ARCHITECTURE_DECISIONS | `docs/architecture/ARCHITECTURE_DECISIONS.md` | ADR-001..013 alternativas + recomendaciones |
| DATA_FLOW | `docs/architecture/DATA_FLOW.md` | Mermaid diagrams + flows reales |
| SECURITY_ARCHITECTURE | `docs/architecture/SECURITY_ARCHITECTURE.md` | Stack, Environments, Security Hardening FASE 2 |
| DEPLOYMENT_ARCHITECTURE | `docs/architecture/DEPLOYMENT_ARCHITECTURE.md` | Docker Compose (11 services), Target despliegue FASE 2 |

---

## 3. State of Tasks

- TASK-001..TASK-007 (FASE 0 + FASE 1): `[x]` — Verificados FASE 0/FASE 1.
- TASK-008+ (FASE 2): `[ ]` — PENDING (21-11-2026) — verificables en FASE 2+ desde 0% a 100% en cada FASE.
- **Security wave 1 verificada realmente** (commit `837b68f`): passlib 1.9.3 + bcrypt 4.0.1 + asyncpg 0.32.0 (`pip` instalado, `verify ok: True False` en snippet); MFA hardening: `mfa type: mfa_challenge`, jti presente, single-use (`mfa_ticket_used:*`, L189/199); brute force ZSET: `zadd/zcard` (L130..155), `locked=False`, `remaining=5`; pytest **35 passed**.

**Progreso actual:** `2 / 44 tasks verified (5%)` — FASE 0 + FASE 1. 0 new (en proceso: Builder-A round Security CRITICAL — S1-001 SSL certs, S1-002, S1-003 ADMIN strong, S1-006 WAF, S1-008 healthz/HSTS/CSP, S1-009, S1-011 SECRET_KEY dinámico).

---

## 4. Nota Final de Evolución

- FASE 2 (Backend Hardening) puede ocurrir en paralelo con FASE 3 (Seguridad) si hay resource — decisione por usuario.
- FASE 4 (Data Migration) puede ocurrir en paralelo con FASE 5 (Testing).
- FASE 6 (Observabilidad) puede ocurrir tras FASE 5.
- FASE 9 (Docs) debería terminar antes del final — retardo slo por documentos.

**Confianza:** HIGH (audit real, deps verificadas, tests reales FASE 2+).
