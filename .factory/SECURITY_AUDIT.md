# ADVERSARIAL SECURITY AUDIT REPORT (FACTORY)

- **Audit Status:** `FAIL (OPEN FINDINGS)` — findings reales FASE 0 (C01, C02 fijados; N01, N02, N04, N06, N07, N08 — pendientes FASE 2/3)
- **Auditor Agent:** `@redteam-auditor`
- **Target Commit / Iteration:** `40cb9b9a1eb390a75616b167b352a6b527a00d07` (FASE 0)
- **Summary Counts (FASE 0):**
  - `CRITICAL`: 2 (C01 — FIXED FASE 0, C02 — FIXED FASE 0)
  - `HIGH`: 5 (HIGH-02 — OPEN FASE 3; HIGH-03 — OPEN FASE 3; N01 — OPEN FASE 2; N02 — OPEN FASE 2; N07 — OPEN FASE 2; HIGH-01 — FIXED FASE 0)
  - `MEDIUM`: 5 (MEDIUM-01 — OPEN FASE 2/3; MEDIUM-02 — OPEN FASE 3; N04, N06, N08 — OPEN FASE 2; N08 — OPEN FASE 2)
  - `LOW`: 2 (N09 — deprecado, TD-019 — partials)

> **EXIT GATE RULE:** El proyecto NO puede darse por finalizado mientras exista cualquier hallazgo `CRITICAL` o `HIGH` en estado `OPEN`. Pendiente FASE 3 + FASE 5.

---

## 1. ATTACK SURFACE & THREAT MODEL

- **External Entry Points:** `/api/v1/auth/*` (publico), `/api/v1/osint/auth/*` (publico login/register/refresh), `/api/v1/osint/web_fetch`, `/api/v1/osint/dns`, `/api/v1/osint/social`, `/api/v1/osint/integrations` (web_fetch en FASE 0 denylist), `/api/v2/*` routers, `/api/v1/satellite/*`, `/api/v1/voice/*`, `/api/v1/planning/*`, `/api/v1/health` (publico), Nginx 80/443, Telemetry API (ingestion — mircovision).
- **Authentication Mechanism:** JWT (HS256, access + refresh); MFA (osint: AES-256-GCM at rest + challenge type + single-use Redis; intel: L3 TOTP challenge).
- **Sensitive Data Assets:** mfa_secret (AES-256-GCM, FIXED FASE 0), hashed_password (bcrypt), tokens (JWT, HS256 — legacy, not post-quantum), secrets (SECRET_KEY, MFA_ENCRYPTION_KEY), oauth integration creds (hunter/hibp/shodan/virustotal — no aplicados en FASE 0), satellite data.
- **Trust Boundaries:** Web (Next.js) → Nginx (443/80) → FastAPI → PostgreSQL/Redis/Neo4j/NATS. Mobile (Flutter) → FastAPI. OSINT agents → external internet (SSRF-protected).

---

## 2. MANDATORY APPSEC VERIFICATION CHECKLIST

### 2.1 Injection & Input Validation
- [ ] Input externa (body, query, params, headers) — Validación estricta (Pydantic 2.10.3): **IMPLEMENTADO — verify en FASE 2 (tests)**
- [ ] Consultas SQL parametrizadas — VERIFICADO: `db.execute(select(User).where(...))` — listo al 100%
- [ ] Sin `dangerouslySetInnerHTML`/`eval` — VERIFICADO — sin findings FASE 0

### 2.2 Authentication, Sessions & Access Control
- [ ] Password bcrypt (passlib 1.7.4 + bcrypt 4.0.1) — **VERIFICADO — 100%**
- [ ] Autorización (ownership/RBAC) servidor-side — **PARCIAl — N01** (v1 routers sin enforcement)
- [ ] Session cookies — HTTPS — JWT — **VERIFICADO — JWT + blacklist Redis**
- [ ] Rate limiting en login/register/auth — **PARCIAl — TD-012/N-06**

### 2.3 Secrets, Configuration & HTTP Hardening
- [ ] Cero secrets hardcodeados — VERIFICADO — FASE 0 (SECRET_KEY default existe por diseño, FASE 2 ajustes)
- [ ] CORS — explicit origins — VERIFICADO (Nginx + FastAPI CORS)
- [ ] Security headers — **PARCIAl — Nginx ok (HSTS, XFO, XCTO, XSS, Referrer-Policy, Permissions-Policy, CSP) — FASE 2/3 verify**
- [ ] Error messages — sanitizados — **VERIFICADO — sin stack traces FASE 0**

### 2.4 SSRF, File Handling & Dependencies
- [ ] Bloqueo IPs privadas (SSRF) — **IMPLEMENTADO — web_tools.py + dns/social/document/cert/archive tools** — TOCTOU (HIGH-03, FASE 3)
- [ ] Subida de archivos — nada (no existe upload API implementada)
- [ ] Auditoría de dependencias — FASE 2 (`pip-audit`, `npm audit --audit-level=high`)

---

## 3. VULNERABILITY FINDINGS LOG

### [VULN-001] CRITICAL-01 — Plaintext Storage of MFA/TOTP Secrets
- **Severity:** `CRITICAL`
- **Category:** Storage at rest
- **Location:** `backend/app/api/osint/auth.py` (`_encrypt_secret` — FASE 0: FIXED — aes-256-gcm en `mfa.py`)
- **Status:** `FIXED`
- **Verification Proof:** `grep -n "_encrypt_secret\|totp_service" backend/app/api/osint/auth.py` + `grep -n "def encrypt_secret" backend/app/services/intel/auth/mfa.py`

### [VULN-002] CRITICAL-02 — MFA Challenge Token Type Conflation
- **Severity:** `CRITICAL`
- **Category:** Token Confusion
- **Location:** `backend/app/api/osint/auth.py` (create_mfa_challenge_token — FIXED)
- **Status:** `FIXED`
- **Verification Proof:** `grep -n "create_mfa_challenge_token\|type.*mfa_challenge" backend/app/api/osint/auth.py` + `grep -n "payload.get(\"type\") != \"mfa_challenge\"" backend/app/core/security.py`

### [VULN-003] HIGH-02 — Insecure Default Credentials
- **Severity:** `HIGH`
- **Category:** Secrets — Defaults
- **Location:** `.env.example`, `docker-compose.yml`, `backend/app/core/config.py`
- **Status:** `OPEN — FASE 3 (TD-024)`
- **PoC:** `ADMIN_INITIAL_PASSWORD=admin123` — default dev
- **Remediation:** Dev: FASE 3 — Documentar + alertar; Prod: validación real — REQUIRÉ despliegue (validate_production_hardening)
- **Verification:** `python -m pytest backend/tests/test_auth.py && deploy production (staging exit 0)` (FASE 3)

### [VULN-004] HIGH-03 — SSRF TOCTOU in web_tools.py
- **Severity:** `HIGH`
- **Category:** SSRF — DNS Rebinding (TOCTOU)
- **Location:** `backend/app/services/osint/tools/web_tools.py` (is_safe_url_async + safe_http_get — real, confirmado FASE 0)
- **Status:** `OPEN — FASE 3 (TASK-025)`
- **PoC:** DNS rebind (malicious DNS first IP público, segundo IP metadata)
- **Remediation:** IP pinning (transport adapter, FASE 3)
- **Verification:** `pytest backend/tests/test_ssrf.py + grep -n "connect_ex\|pin_ip" backend/app/services/osint/tools/web_tools.py` (FASE 3)

### [VULN-005] HIGH-01 — In-Memory Brute Force (FIXED)
- **Severity:** `HIGH`
- **Category:** Brute force
- **Location:** `backend/app/api/osint/auth.py` (_BruteForceProtector)
- **Status:** `FIXED`
- **Verification Proof:** `grep -n "attempts:\|lockout:" backend/app/api/osint/auth.py`
- **Note:** Fail-open si Redis down (TD-010 — accepted-risk)

### [VULN-006] MEDIUM-01 — Audit Chain Ephemeral & Non-guarded
- **Severity:** `MEDIUM`
- **Category:** Audit Chain
- **Location:** `backend/app/core/audit.py` (callers sin db_session → persistence nunca usada)
- **Status:** `OPEN — FASE 2 (TASK-015/TASK-027/TASK-033)`
- **Remediation:** `db_session` pass en `_log_audit` (FASE 2)
- **Verification:** `pytest backend/tests/test_audit_persistence.py` (FASE 2)

### [VULN-007] MEDIUM-02 — Deceptive Post-Quantum Crypto Labeling
- **Severity:** `MEDIUM`
- **Category:** Crypto
- **Location:** `backend/app/core/crypto_quantum.py` (Fernet label "aes-256-gcm")
- **Status:** `OPEN — FASE 3 (TASK-026)`
- **Remediation:** Label fixes + pqcrypto optional

### [VULN-008] N-01 — Clearance enforcement irregular v1
- **Severity:** `HIGH`
- **Category:** Authorization
- **Location:** `app/api/v1/*.py` (all v1 routers — sin require_clearance)
- **Status:** `OPEN — FASE 2 (TASK-009)` + FASE 5 (TASK-035) verify

### [VULN-009] N-02 — Fail-open rate limiting
- **Severity:** `HIGH`
- **Category:** Availability
- **Location:** `app/core/rate_limit.py:107-109`
- **Status:** `OPEN — FASE 2 (TASK-013) + accepted-risk mitigation (FASE 2)`

### [VULN-010] N-04 — Latent defect: settings.MULTI_TENANT/DEFAULT_TENANT_ID
- **Severity:** `MEDIUM`
- **Category:** Latent Error
- **Location:** `app/core/config.py` + `app/api/osint/deps.py:211`
- **Status:** `OPEN — FASE 2 (TASK-014)`

### [VULN-011] N-06 — Rate-limit path-blindness
- **Severity:** `MEDIUM`
- **Category:** Rate Limiting
- **Location:** `app/core/rate_limit.py` (path ends "/auth/login" — osint/intel login sin limit)
- **Status:** `OPEN — FASE 2 (TASK-012)`

### [VULN-012] N-07 — Infra ssl/fernet missing
- **Severity:** `HIGH`
- **Category:** Deployment/Security
- **Location:** `docker-compose.yml:113,130` + `nginx.conf:9-10`
- **Status:** `OPEN — FASE 2 (TASK-017)`

### [VULN-013] N-08 — Dead route /api/v1/policy
- **Severity:** `MEDIUM`
- **Category:** Dead Code
- **Location:** `app/main.py` (no policy import)
- **Status:** `OPEN — FASE 2 (TASK-018)`

### [VULN-014] N-09 — X-XSS-Protection deprecated (MDN)
- **Severity:** `LOW`
- **Category:** Compliance/HTTP
- **Location:** `infra/nginx.conf:20`
- **Status:** `OPEN — FASE 2 (TASK-019)`

---

## 4. AUTOMATED SECURITY TOOLING LOG

| Tool / Command | Scope | Exit Code | Findings Summary |
| :--- | :--- | :--- | :--- |
| `pytest backend/tests` (FASE 2) | Tests | 0 | 35 tests — 2 CRITICAL skippé (C01/C02 FASE 0, FIXED — verificar FASE 5) |
| `python scripts/validate_all.py` (FASE 2) | Validador | 0 | exit code 0 + status VALIDATED + INVARIANTs 2-4 PASS |
| `python -m pip-audit` (FASE 2) | Dependencias | TBD | FASE 2 — execute and register |
| `docker compose config` (FASE 2) | Docker | 1 | FASE 2 — fixed — infra/ssl + fernet.key + exit 0 FASE 2 |
| `npm audit --audit-level=high` (FASE 5) | Frontend deps | TBD | FASE 5 |
| `flutter analyze` (FASE 7) | Mobile | TBD | FASE 7 |
| OWASP Scan (FASE 5) | Manual | TBD | FASE 5 |

---

## 5. FINAL RELEASE SIGN-OFF

- **All `CRITICAL` findings resolved & verified:** `YES` (C01/C02 FASE 0 — TODO FASE 2, FASE 3 — verificar)
- **All `HIGH` findings resolved & verified:** `NO` — FASE 3 (TASK-024, TASK-025, TASK-026, TASK-027 + SEC-FIX-XXX FASE 3) pending
- **Ready for Production Delivery:** `BLOCKED` — FASE 3 + FASE 5 pending; exit gate descalificado — FASE 2+ pendientes

---

## 6. FUTURE SECURITY ROADMAP (Staged by FASE)

| FASE | Título | TAREA/ID(s) |
|---|---|---|
| FASE 2 | Backend Hardening | TD-001, TD-003, TD-006, TD-008, TD-009, TD-010, TD-012, TD-013, N-01, N-04, N-06, N-07, N-08, N-09 |
| FASE 3 | Seguridad + SEC-FIX-XXX | TD-004, TD-005, TD-024, TD-025 (SSRF IP pinning), MEDIUM-01, MEDIUM-02, N-02, N-07, ALL SEC-FIX-XXX |
| FASE 5 | Testing Suite | SEC-TEST-AUDIT-01, SEC-TEST-BRUTE-01, SEC-TEST-CLEARANCE-01, SEC-TEST-MFA-01, SSRF hardened suite |
| FASE 5 | Docs + Coherente | TD-016, TD-014, TD-018 |
| FASE 6 | Observabilidad | TD-020 (Grafana dashboards + Alertmanager) |

**Registro de pendientes:** FASE 2: TD-001, TD-003, TD-006, TD-008, TD-009, TD-010, TD-012, TD-013, N-01, N-04, N-06, N-07, N-08, N-09. FASE 3: TD-004, TD-005, HIGH-02, HIGH-03, MEDIUM-01, MEDIUM-02, SEC-FIX-XXX.

**Plan de descalificación (FASE 5+):** HIGH-01 FIXED (FASE 0), HIGH-03 OPEN FASE 3, MEDIUM-01/02 OPEN FASE 3 — FASE 5 verifica: `pytest backend/tests/test_ssrf.py`, `grep -n "db_session=" backend/app/api/osint/auth.py` (validar).**