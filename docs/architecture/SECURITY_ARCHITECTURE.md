# SECURITY_ARCHITECTURE.md — Arquitectura de Seguridad (FASE 1)

**Doc ID:** ARCH-SEC-001 | **Estado:** FASE 1 — TARGET (diseño de FASE 1, AS-IS FASE 0)
**Fecha:** 21-11-2026

> **Modelo:** FASE 0 confirmó: osint auth FIXED (AES-256-GCM + tickets isolados + Redis single-use), SSRF denylist real, rate-limit Redis. FASE 0 OPEN: HIGH-02 defaults, SSRF TOCTOU, audit chain persistence, quantum label. FASE 1 y FASE 3 documentan path.

---

## 1. Visión General (AS-IS → TARGET)

| Layer | AS-IS Real | TARGET |
|---|---|---|
| **Auth** | JWT HS256, access+refresh, 3 routers fragmentados, osint MFA AES-256-GCM FIXED, intel L3 challenge, persistence legacy sin MFA, clearance v2 uniformizado, v1 sin enforcement | Consolidar en un solo router, uniformizar enforcement v1, clearance hierarchy Open fully |
| **Seguridad Network (SSRF)** | web_tools.py denylist completo + TOCTOU (HIGH-03) | IP pinning socket-level, DLQ, redirect hardening |
| **Crypto** | Fernet labeling "aes-256-gcm" (FALSE), no pqcrypto (MEDIUM-02) | Labels honestos + pqcrypto opcional + AESGCM labels reales |
| **Secrets mgmt** | Secrets: FERNET_KEY_PATH default ./fernet.key, falta en repo (TD-007) |infra/ssl + fernet.key scripts + docs |
| **Audit Chain** | In-memory (TD-002) | Persistência real + persistência + verify_chain + publish events |
| **Infra hardening** | Nginx hardening presente, Docker compose falla (missing infra/ssl) | SSL/key management, healthcheck architecture, CIS hardening guide |

---

## 2. Control Maturity (FASE 0 AS-IS)

| Control | AS-IS Real | Status | Nota |
|---|---|---|---|
| Authn/Authz enforcement (clearance) | V2 enforce + v1 partial (N-01) | PARTIAL | New: uniformizar enforcement v1 |
| Identificación | 3 User models + fragmentation (TD-001) | PARTIAL | Unificación FASE 2 |
| JWT tokens (HS256, access/refresh, MFA) | Implemented (osint FIXED) | Implemented | Legacy auth de osint solucionado |
| SSRF protections | Denylist real + TOCTOU (HIGH-03 parc) | PARTIAL | IP pinning FASE 3 |
| Rate limiting | Redis sliding window + global nginx limiter (N-02 fail-open) | PARTIAL | Fix FASE 2 + circuit breaker |
| Audit trails | In-memory (no DB) + 1 tamper-proof claims | PARTIAL | Persistência FASE 2 + tamper detection FASE 3 |
| HSM | Fernet_key - no functional | PARTIAL | Literal stack change (no natural) |
| Secrets Management | MFA_ENCRYPTION_KEY (valid, altura inicial) | PARTIAL | Key rotation + hardening FASE 2 |
| CSP/HSTS/Headers | Nginx: HSTS, XFO, XCTO, XSS, Referrer-Policy, Permissions-Policy, CSP | OK | Hardening adding SESIS-specific: CSP y tls 2.2+ |
| TLS 1.3 | TLS1.2+TLS1.3 | OK | Exportable dev + Self-signed + tracking |
| GeoBlock (C2) | — | OPEN FASE 4 | Añadir by_ip/country blocking (closed set incluid o.g.) |

---

## 3. Logica de Seguridad (Real → TARGET)

### 3.1 Autenticación — Arquitectura Consolidada (ADR-004)

**AS-IS:**
- `/api/v1/auth/*` — Legacy JWT (persistence, sin MFA, sin brute-force real, sin refresh rotation por user)
- `/api/v1/osint/auth/*` — MFA AES-256-GCM (FIXED) + tickets isolados (type="mfa_challenge" + single-use Redis) + Redis brute-force
- `/api/v1/intel/auth/*` — L3 TOTP challenge

**TARGET:**
- Unified Auth Router — `/api/v1/auth/*` — uniformización, clearance enforcement uniform, allow MFA, JWT access/refresh rotate, blacklist JTI real, etc.

### 3.2 Seguridad de Red (SSRF — ADR-005, FASE 3)

**AS-IS:**
- `is_safe_url_async` — resolve DNS validando (TOCTOU)
- `safe_http_get` — validación por lote + redirects (5 max) — funcional

**TARGET (FASE 3):**
- IP pinning: transport adapter validando IPs en socket connect
- WAF: blocker externo (Envoy/nginx) para SSRF
- Full redirect hardening + new DNS servers
- Natural exposure monitoring + alerts

### 3.3 Control de Acceso — Uniformizado (ADR-006, N-01)

**AS-IS:**
- `require_clearance` — v2 routers (c2, space, border, logistics, cyber, ew) + policy.evaluate
- v1 routers — sin enforcement (N-01)

**TARGET:**
- Uniformizar clearance enforcement en v1 — barrido routers + tests (SEC-TEST-CLEARANCE-01..08)
- Fail-closed

### 3.4 Auditoría — Persistence Real (FASE 2)

**AS-IS:**
- In-memory AuditChain (core/audit.py), memoria + hash chain
- `_log_audit` — sin db_session → persistence nunca usada

**TARGET (FASE 2):**
- AuditChain persistence — queries a PostgreSQL cada hash cambia
- Concurrent operations — `asyncio.Lock` + natural exp
- Natural tampering detection — `verify_chain()` + FASE 5 tests

### 3.5 Señales (NLU/Dialogs, FASE 2)

- Identificación de signals — verificar (TBD FASE 2)

### 3.6 Encryption de datos at rest (FASE 2-3)

- AESGCM labels: mfa secrets (mfa.py AESGCM), messages (services/messaging?), bulk exports
- Fernet legacy: labels fake → fix (crypto_quantum.py)

---

## 4. Matriz de Pruebas de Seguridad (Real — FASE 0 + FASE 5 Proposto)

| ID | Título | Severidad | Status FASE 0 | Target FASE 5 |
|---|---|---|---|---|
| SEC-TEST-MFA-01 | MFA secrets encrypted + challenge isolation | CRITICAL | IMPLEMENTADO (ver test_mfa_security.py) | VERIFY (FASE 2) |
| SEC-TEST-BRUTE-01 | Distributed Brute-Force Lockout | HIGH | IMPLEMENTADO (ver test_rate_limit.py) | VERIFY (FASE 2) |
| SEC-TEST-CLEARANCE-01 | Classification & Clearance Enforcement | HIGH | **NEW — 0 enforcement v1** | 0% (FASE 2) |
| SEC-TEST-AUDIT-01 | Audit Chain integrity + persistence | MEDIUM | 0% en FASE 0 | NEW (FASE 5) |
| SEC-TEST-SSRF-01 | SSRF hardened + DNS rebinding | MEDIUM | PARTIAL | STRICTER (FASE 5) |
| SEC-TEST-DOC-01 | Documentación update SHINE | MEDIUM | Open | regenerate docs FASE 9 |
| N-01 | Clearance enforcement irregular v1 | HIGH | OPEN | FIXED FASE 2 |
| N-02 | Fail-open rate limiting | HIGH | OPEN (accepted-risk) | Documentar FASE 2 |
| N-03 | EncryptedField silent fallback | MEDIUM | OPEN | fix FASE 2 |
| N-04 | Latent require_tenant_access | MEDIUM | OPEN | fix FASE 2 |
| N-06 | Rate limiting path-blindness | MEDIUM | OPEN | fix FASE 2 |
| N-07 | Infra ssl/fernet missing | HIGH | OPEN | fix FASE 2 |
| N-08 | Dead route /api/v1/policy | MEDIUM | OPEN | fix FASE 2 |
| N-09 | X-XSS-Protection deprecated (MDN) | LOW | OPEN | FASE 2 fix |

---

## 5. Hardening roadmap (FASE 0 → FASE 3)

| Fase | Título | TD/N-ID | Status |
|---|---|---|---|
| FASE 2 | Backend Hardening | TD-001, TD-002, N-01, N-02, N-03, N-04, N-06, N-07, N-08 | Descripción detallada en TASKS.md |
| FASE 3 | Seguridad (SEC-FIX-XXX + todos finding crítico) | ALL | Descripción detallada en TASKS.md |
| FASE 5 | Test full matrix + persistence tests | ALL SEC-TEST-XXX | Descripción detallada en TASKS.md |

---

## 6. Pruebas en CI/CD (FASE 4 - OPEN)

- [ ] Add to GH Actions: pip-audit, gitleaks, sonarcloud, pytest backend/tests
- [ ] Add SAST scan (bandit) + Semgrep rules

---

## 7. References

- `docs/audit/SECURITY_AUDIT.md` — FASE 0 audit (finding list real)
- `docs/SECURITY_ARCHITECTURE.md` — SmartNationdefense — arquitectura de seguridad real (diseño de FASE 1)
- `docs/SECURITY_AUDIT.md` — audit de referencia (baseline — SmartNationdefense audit — a revisar/validar FASE 5)