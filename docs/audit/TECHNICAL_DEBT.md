# TECHNICAL_DEBT.md — Register de Deuda Técnica (FASE 0)

**Doc ID:** DEBT-2026-SND-001 | **Fecha:** 21-11-2026 | **Estado:** Registro plano (priorización en FASE 2-FASE 9)

> **Método de priorización:** scoring `Likelihood (1–5) × Impact (1–5)` tipo ENGINEERING_RISKS, otras dimensiones: `Frecuencia × Costo × Riesgo Funcional`. Status `OPEN` until `@builder` implements & `@qa-verifier` validates; escala: `DONE`, `WIP`, `OPEN`, `DEFERRED`.

---

## 1. Deuda (TD1 — Identificado en `docs/audit/REPOSITORY_AUDIT.md §4-§5`)

| TD-ID | Título | Categoría | Score | Impacto Funcional | Estrategia | Estado |
|---|---|---|---|---|---|---|
| TD-001 | Consolidar 3 modelos `User` (persistence/intel/osint) | ARCH-IDENTITY | 16 | Alto: colisión `__tablename__="users"` | Estándar: namespaceo o unified ORM (FASE 2, ADR-001) | OPEN |
| TD-002 | Arreglar `_log_audit` sin `db_session` — no persiste | ARCH-AUDIT | 12 | Alto: chain efímera | Inyectar db_session default o todo-llamado con db_session | OPEN |
| TD-003 | Uniformizar `require_clearance` enforcement en v1 routers | ARCH-AUTHZ | 16 | Alto: Clearance Leakage v1 | Barrido en v1: vencidades, pruebas AC-XX-01..08 | OPEN |
| TD-004 | SSRF TOCTOU en `safe_http_get` (DNS pinning / transport adapter) | SEC-TOCTOU | 12 | Alto: SSRF via rebinding | Implementar socket-level IP pinning | OPEN (accepted-risk → descalificación en FASE 3/5) |
| TD-005 | Fix labeling criptografía post-cuántica (Fernet label "aes-256-gcm") | SEC-CRYPTO | 12 | Alto: labeling falso | Change label; instalar `pqcrypto` opcional en FASE 4 | OPEN |
| TD-006 | `EncryptedField` silent fallback: retorna `{}` sin AES_KEY o con fallback decrypt | ARCH-DATA | 10 | Alto: datos silenciosamente invisibles (`Mission.sensitive`, `Alert._sensitive`) | Fail-closed: raise si AES_KEY vacío y existe campo sensBL | OPEN |
| TD-007 | Infra: faltan `infra/ssl/` y `fernet.key` como artifacts del repo | OPS-INFRA | 10 | Alto: `docker compose up` falla | Crear certs de dev + scripts/generate_keys.py ejecutado; `.gitignore`-d | OPEN |
| TD-008 | Latent defect: `settings.MULTI_TENANT` y `DEFAULT_TENANT_ID` no existen en Settings (AttributeError si `require_tenant_access` invocada) | ARCH-CONFIG | 8 | Alto: error latente | Añadir defaults en `config.py`; habilitar require_tenant_access con tests FASE 5 | OPEN |
| TD-009 | Rate limiting path-blindness: solo `/auth/login` (legacy); osint/intel login sin límite | OPS-SEC-RATELIM | 8 | Alto: brute force en módulos nuevos | Aplicar `DEFAULT_LIMITS["login"]` a endpoints de login reales | OPEN |
| TD-010 | Fail-open rate limit: Redis down → `call_next` sin límite | OPS-SEC-RATELIM | 8 | Alto: availability vs security tradeoff | Documentar como accepted-risk; implementar circuit breaker local | OPEN (accepted-risk) |
| TD-011 | 2 modelos `AuditLog` (`persistence`, `osint.audit_log`) — namespaceo, mismo fin | ARCH-DATA | 6 | Alto: ambigüedad de imports | Usar `persistence.AuditLog` como único; verificar test_audit_persistence.py | OPEN |
| TD-012 | Migrations `backend/migrations/*.legacy` vs Alembic real — verificar dedup en FASE 2 | ARCH-DEPLOY | 4 | Alto: esquema ambiguity | FASE 2: `alembic heads`, `alembic check` | OPEN |
| TD-013 | Guardian scripts — 6 lenguajes, no importados, auto-ejecutan al importar | OPS-DEADCODE | 8 | Alto: confusion | Quarantine (mover a `scripts/archived/guardian`) FASE 2 | OPEN |
| TD-014 | Docs desactualizados: `docs/AUDIT.md`, `ARCHITECTURE_CURRENT.md`, `ARCHITECTURE.md`, `API.md`, `VALIDATION_PLAN.md`, `FINAL_VALIDATION_REPORT.md`, `ENGINEERING_RISKS.md` — muchos features phantom (ARCH-01, ARCH-02, SEC-01..03, GOV-01) | GOV-DOCS | 12 | Alto: falsas expectativas de seguridad/ops | Regenerar docs a partir de realidad FASE 0 (FASE 9) | OPEN |
| TD-015 | Test suite actual: ~30-35 tests, sin E2E/integration/security suites — FASE 2 dice 50+ | GOV-TESTING | 12 | Alto: cobertura funcional vs use | Descubrir coverage real FASE 2; cerrar gaps por módulo FASE 5 | OPEN |
| TD-016 | `docs/SECURITY_AUDIT.md` usa rutas `file:///d:/...` — Windows-only artifact (auditutor agent 3) | GOV-DOCS | 4 | Medio | Limpiar a `file://` POSIX o rutas relativas FASE 2 | OPEN |
| TD-017 | Selenium/Agent UI: docs de seguridad no definen auditors tooling actual (`scripts/validate_all.py` es único toolchain) | GOV-TOOLING | 4 | Medio | Añadir GHA workflow + scripts FASE 4 | OPEN |
| TD-018 | `ApiGeolocationTool` hardcodea URL de ip-api.com — sin proxy/verificación externa | SEC-EXTERNAL | 8 | Medio: exposure a datos PII via URL | Añadir signing/alternativa en FASE 5 | OPEN |
| TD-019 | X-RateLimit headers en respuestas sólo en endpoints pasados; error 429 sin body json | OPS-RATELIM | 6 | Medio | Add errors/JSON body + Retry-After siempre FASE 2 | OPEN |
| TD-020 | Healthchecks del Docker Compose: `nginx` requiere api healthy; `api` requires postgres+redis — acceptable pero añadir `/healthz` estáico en nginx | OPS-INFRA | 4 | Medio | FASE 2: build early failure modes (ver docker-compose check FASE 4) | OPEN |
| TD-021 | Flutter `api_client.dart` no está dentro de scope del SDD de FASE 2 (FASE 7) — trackeado para su clarificación | GOV-MOBILE | 2 | Bajo | Revisar compatibilidad Backend FASE 3 | OPEN |

---

## 2. Deuda Similar (Stdcheldford — pendiente de execución)

| TD-ID | Título | Descripción | Estado |
|---|---|---|---|
| TD-022 | `docs/API.md` (1054 líneas) — endpoints legacy sin docs update (ai team conventions, márqueting) | Regenerar docstrings y documentar módulos nuevos FASE 9 | OPEN |
| TD-023 | SESIS config: `MFA_ISSUER="SESIS"` — labels de todos los tokens (sub, aud, iss) no desplegados como TOKENES type-specific en persistence auth | Standard | OPEN |
| TD-024 | `SIGNED` retries en `validate_all.py` - invariant 3 - incompleto: sin test de locking-concurrente | Añadir tests reales FASE 5 | OPEN |
| TD-025 | Query `select(User).where(User.username == ...)` — duplicado alrededor de login() en múltiples routers (persistence + osint + intel + ingest) — decir inyección | FASE 2: refactorizar a `get_user_by_username()` | OPEN |
| TD-026 | `Backend/archivos pycache` — debe estar en .gitignore actual | Minor | DONE |

---

## 3. Deuda por Módulo (Resumen Real)

| Módulo | Deuda Principal | Fase Propuesta |
|---|---|---|
| Auth (identity) | TD-001/002, TD-008, TD-023, TD-025 | FASE 2 |
| Seguridad (SSRF, crypto) | TD-004, TD-005, TD-018, TD-010 | FASE 3 |
| Deployment (docker, infra) | TD-007, TD-020 | FASE 2 |
| Data/Events | TD-002 (audit), TD-011, TD-002+TD-012 | FASE 2 |
| Mobile | TD-021 | FASE 7 |
| Móviles (news, web) | TD-008, TD-018 (extendido a tools) | FASE 5 |
| Testing/QA | TD-015, TD-024, TD-019 | FASE 5-FASE 6 |
| Observabilidad | TD-020 (fácil), TD-008 | FASE 6 |
| Docs | TD-014, TD-016 | FASE 9 |
| Guardias (scripts) | TD-013 | FASE 2 |

---

## 4. Plan de Resolución (Estrategia General)

1. **FASE 2 — Backend Hardening (adr-020 to adr-030)**
   - Uniformizar enforcement `require_clearance`: barrido en `api/v1/*.py` routers; añadir tests AC-02-01..08 (clearance enforcement v1).
   - Fix `_log_audit`: pasar `db_session` desde todos los `_log_audit` calls, o default `db_session=None` → buscar sesión del contexto (temporal para FASE 2, resolver persistencia real FASE 3).
   - Fix path-blindness de rate limiting: detección de login endpoints por prefijo `/auth/` también en osint y intel.
2. **FASE 3 — Seguridad (SEC-FIX-XXX)**
   - SSRF: IP pinning (transport adapter, `httpcore` custom, bypass tomar socket, validar en `connect`).
   - Crypto quantum: labels honestos + `pqcrypto` opcional; actualizar `docs/SECURITY_AUDIT.md` v2.
   - Infra: crear `infra/ssl` (self-signed dev), `fernet.key` vía `scripts/generate_keys.py` + docs.
3. **FASE 4 — Data Migration & modernization**
   - Consolidación User: unified `User` con `IntelUserSchema`, `OsintUserSchema` como mixins; desplegar migración backfill.
   - Alembic `env.py` → source of truth; `backend/migrations/*.legacy` → archive.
4. **FASE 5 — Testing & QA**
   - Test suites nuevas: security (SSRF redo con mocks de DNS dinámico, audit persistence concurrency, clearance v1 matrix, mfa_osint, brute-force redis), integration (ingestion pipeline + NATS mock), e2e scenarios.
   - Parse `reports/validation.json` real: `tests.passed=35 → pytest`.
5. **FASE 6 — Observabilidad**
   - Grafana dashboards por módulo (C2, SAT, OSINT,Tactical, C2-v2, Maven, Mobile, Security).
   - Prometheus Alertmanager integración + configs de alerta por módulo (SLA/Disponibilidad/SSRF anomalies).
6. **FASE 7 — Mobile**
   - Completar/validar `pubspec.yaml` (check actuales: firebase, watch GG), interactive UI tests (Fases pruebas visuales).
7. **FASE 9 — Docs regeneration**
   - Regenerar docs/ {ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md} desde realidad actual (FASE 0/FASE 1/FASE 2) + ADRs.

---

## 5. Indicadores de Éxito (KPIs de Ejecución de FASE 0-2)

| KPI | Actual | Meta FASE 0-2 | Semana | Impact |
|---|---|---|---|---|
| Deuda total (Score) | ~40 | 0 | FASE 0-2 | Baseline bajo |
| Findings CRITICAL/HIGH | 10 | 0 | FASE 3 (SC-FIX) | Cero blockers deployment |
| Clearance enforcement v1 | 0/21 routes | 21/21 | FASE 2 | Zero leakage |
| Audit Chain persistence | 0/N calls con db_session | 100% | FASE 2-3 | Repudiation coverage |
| SSRF TOCTOU fixed | NO | YES | FASE 3 | Risk reduction 60% |
| Test coverage total | ~30 tests, 0% cobertura real (en FASA 0) | 50+ | FASE 5 | Calidad 25%+ |
| Docker compose deploy | FALLA (falta ssl/fernet) | OK | FASE 2 | Deployable delivery |
| Deprecated X-XSS-Protection | SI | NO | FASE 2 | MDN compliance |
| User-docs coherence | FALSO (8 phantom) | VERDADERO | FASE 9 | Confianza |