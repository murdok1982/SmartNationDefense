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
| TDEC-014 | **Uniformización `require_clearance("RESTRICTED")` enforcement en routers v1 (TASK-009)** — enforcement explícito añadido a handlers que lo faltaban (B-D3 op. 1: reafirmar enforcement en más handlers donde falte enforcement explícito) | FASE 2 | (1) reafirmar enforcement en handlers sin enforcement; alinear laberinto para uniformidad | Routers v1 sin enforcement antes: aar(6), brain(5), fusion(4), intel(7), logistics(7), map(9), messaging(6), planning(11), prediction(5), reports(6), sensors(6), terrain(5), voice(3) = 80 handlers; +80 `principal: dict = Depends(require_clearance("RESTRICTED"))`; imports `Depends`/`require_clearance` añadidos en 13 archivos; brain/intel/sensors mantienen deps personalizados (require_confidential_clearance / require_restricted_clearance / require_operator_key) + reafirmación uniforme; brain: ¿Riesgo API-key vs JWT documentado — la unified-auth ADR-004 es el camino correcto para v2 | REAL: `cd backend && python3 -m py_compile <13 archivos>` OK; `grep -rnE "require_clearance\(" backend/app/api/v1/ --include=*.py | wc -l` → 89; `cd backend && python3 -m pytest tests/test_clearance_enforcement.py -q` → 5 passed; `cd backend && python3 -m pytest tests/ -q` → 35 passed | `DONE (TASK-009)` |

| TDEC-015 | **Closure HIGH-03/VULN-005: SSRF en visión/Maven** — `SatelliteAnalyst` descargaba `image_url`/`frame_url` con `follow_redirects=True` sin validación | FASE 3 | (1) confiar en la allowlist de hostnames; (2) reutilizar `safe_http_get` con IP pinning por salto | Riesgo real: acceso a metadata cloud (`169.254.169.254`) con cualquier JWT. Elijo (2) por defensa en profundidad; límite 25 MB, sin `follow_redirects`, 500 sin `str(e)` | REAL: `pytest tests/test_vision_ssrf.py` → 10 passed (metadata, loopback, RFC1918, IPv6, v4-mapped, file/gopher) | `DONE (SEC-FIX-002)` |
| TDEC-016 | **Postura ante caída de Redis** — antes fail-open silencioso (rate-limit permitía todo; `is_jti_revoked` devolvía False) | FASE 3 | (1) mantener fail-open + alerta; (2) fail-closed en staging/production con abort de arranque | Elijo (2) para sistemas clasificados: sin Redis no se puede demostrar no-revocación ni limitar abuso; dev conserva fail-open para DX | REAL: `test_rate_limit_hardening.py` (503 sin `call_next`) + `test_security_core.py` (dev open / prod 503); suite 157 passed; métrica `sesis_security_fail_open_total` | `DONE (SEC-FIX-001)` |
| TDEC-017 | **Identidad del cliente tras Nginx** — `request.client.host` era la IP del proxy → bucket global 100 req/min (DoS) | FASE 3 | (1) confiar en `X-Forwarded-For` siempre; (2) allowlist de proxies de confianza (`TRUSTED_PROXIES`) + bucket por `sub` | Elijo (2): (1) permite spoofing trivial de IP y bypass de rate-limit. Default loopback + RFC1918 (compose), configurable | REAL: 4 tests de `resolve_client_ip` (spoof ignorado) + bucket `sub` independiente | `DONE (SEC-FIX-004)` |
| TDEC-018 | **Lockout de login en el router activo** — el protector existía sólo en `app/api/osint/auth.py` (router no montado) | FASE 3 | (1) montar osint/auth; (2) reutilizar el protector en `/api/v1/auth/login` | Elijo (2): montar osint/auth expondría endpoints duplicados sin revisar; reutilizar mantiene una sola fuente de lockout path-aware | REAL: `test_login_lockout.py` (429 + Retry-After; AuditLog persistido); suite 157 passed | `DONE (SEC-FIX-005)` |
| TDEC-019 | **Dependencias con advisories** — torch 2.5.1 (CRITICAL torch.load), next 14 EOL, jose/multipart/crypto/lxml desactualizados | FASE 3 | (1) actualizar todo en un solo commit; (2) retirar torch del runtime + upgrades puntuales + SCA bloqueante con allowlist | Elijo (2): torch sólo se usa en visión opcional; sacarlo elimina el CVE sin 2 GB de runtime. Next sube a rama con parche; advisories sin fix se documentan | REAL: pip-audit con allowlist = 0 vulnerabilities; YOLO exige sha256 y prohíbe descarga en production; CI con pip-audit + npm audit | `PARCIAL (SEC-FIX-006)` |

---

## 2. Decisiones Incorrectas (Datos reales de FASE 0, seriemt os presentiause en FASE 0 para mejora FASE 2)

| ID | Decisión (incorrecta/controvertida) | Alternativa mejorada | Estado | Notas |
|---|---|---|---|---|
| INC-01 | **Documentar MicroVM Sandbox** en compliance (`compliance/ENS_ALTA_matrix.md`) | Aceptar como EXPERIMENTAL (N-14, FASE 9) | `FIXED — FASE 0` (TASK-001: compliance regenerado + honesto) | FASE 9: regenerar compliance matrices honestas |
| INC-02 | **Aceptar default ADMIN_INITIAL_PASSWORD=admin123** en dev | Desplegar producción con validate_production_hardening + FASE 3 rotate | `FIXED — FASE 3 (SEC-FIX-003)` | User preference (dev leniency vs dev/staging) — DOCUMENTAR EXPLICITAMENTE |
| INC-03 | **Aceptar default POSTGRES_PASSWORD=change-me-in-production** | Rotar al deploy de staging/prod (FASE 3) + docs (FASE 9) | `FIXED — FASE 3 (SEC-FIX-003)` | |
| INC-04 | **Label "Fernet" como "aes-256-gcm"** (MEDIUM-02) | Labels honestos (Fernet=AES-128-CBC+HMAC) | `FIXED — FASE 3 (TASK-026)` | crypto_quantum.py |
| INC-05 | **Envio Múltiple User models en tabla `users`** | Namespaceo tablas (FASE 2 — intel_users, osint_users) o unified User | `FIXED — FASE 2 (TASK-008, TD-001)` | |
| INC-06 | **Fail-open rate limiting** (N-02) | Disable open circuit + documentar + circuit breaker FASE 2 | `FIXED — FASE 3 (SEC-FIX-001: SECURITY_FAIL_MODE=closed en staging/prod)` | |
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