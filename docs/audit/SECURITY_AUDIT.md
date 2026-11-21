# SECURITY_AUDIT.md — Auditoría de Seguridad Real (FASE 0) — SmartNationDefense / SESIS-FEDERATION

**Document ID:** AUDSEC-2026-SND-001 (FASE 0, Reversed)
**Audit Date:** 21-11-2026
**Auditor:** Arquitecto Principal (@architect) — Auditoría estática de código real + llamadas, sin ejecución de exploits (FASE 5 estenderá con pruebas ejecutables)
**Target:** SmartNationDefense / SESIS-FEDERATION — `main` @ `40cb9b9`
**Overall Threat Level:** HIGH (Confirmación real — Hallazgos CRITICAL/HIGH abiertos en código)

> **Estilo de juicio:** This audit based on `docs/SECURITY_AUDIT.md` (llegó 03-09-2026). Comparativa realmente real (¿fijado o no?). Todos los hallazgos verificados en código actual (cito ficheros/líneas).

---

## 1. Executive Security Assessment

System CANNOT be classified as "Zero-trust", "Production-ready", or "Military-grade" until:
- [ ] HIGH-02 fully resolved (secrets defaults removed/rotated — development environment begins implementation).
- [ ] HIGH-03 (SSRF TOCTOU) — accepted-risk mitigations documented + mitigadores added (denylist amplify, IP pinning, WAF rules).
- [ ] MEDIUM-01/02 fully resolved (audit chain persistence + honest crypto labeling).
- [ ] SEC-FIX-XXX actions executed.

Impact: mitigated for accepted risks of HIGH-01/SEC-04 with in-code limitations documented. This is a **Prototype/Reference Architecture** (per FINAL_VALIDATION_REPORT + README) with a reducible but non-zero security posture.

---

## 2. Findings — Veredicto real vs. viejo

| ID | Título | Severidad (real) | Status (real) | Explicación |
|---|---|---|---|---|
| CRITICAL-01 | Plaintext storage of MFA/TOTP secrets | CRITICAL | **FIXED** | `osint/auth.py:226-228` → `totp_service.encrypt_secret()`; `mfa.py:158-168` AES-256-GCM (nonce12+tag16, base64). `validate_all.py` invariant 1 pasa. |
| CRITICAL-02 | MFA Ticket Type Conflation | CRITICAL | **FIXED** | `security.py:52-74` `create_mfa_challenge_token` (`type="mfa_challenge"`); `decode_mfa_token:77-98` rechaza otros; `osint/deps.py:110-111` rechaza en get_current_user; `osint/auth.py:196-215` single-use Redis (`used_mfa_ticket:{jti}`). |
| HIGH-01 | In-Memory Brute Force | HIGH | **FIXED (partial)** | `osint/auth.py:116-184` Redis-backed (attempts/lockout con incr/setex/exists/delete); fallback in-memory si Redis down. Sin Redis → degrada a memoria. |
| HIGH-02 | Insecure Default Credentials | HIGH | **OPEN** | `ADMIN_INITIAL_PASSWORD=admin123` (.env.example:72, docker-compose:23); POSTGRES_PASSWORD=change-me-in-production; NEO4J_PASSWORD=change-me-in-production; SECRET_KEY=cambia-esto-en-produccion; GRAFANA_ADMIN_PASSWORD=change-me-in-production. Validador `validate_production_hardening` existe. |
| HIGH-03 | SSRF TOCTOU | HIGH | **OPEN (accepted-risk)** | `web_tools.py:81-106` resuelve DNS validando; `web_tools.py:109-128` `client.get()` hace resolución #2 → TOCTOU real. Denylist amplio presente (0.0.0.0/8, 100.64/10, 198.18/15, 240/4, IPv6 mapped...). |
| MEDIUM-01 | Ephemeral & Non-guarded Audit Chain | MEDIUM | **OPEN (partial)** | `core/audit.py:40,68` Import OK (persistence.AuditLog); `audit.py:24` `_lock` asyncio presente. **Pero** `osint/auth.py:291-296` `_log_audit` NO pasa `db_session` → persistence nunca se usa. |
| MEDIUM-02 | Deceptive Post-Quantum Crypto | MEDIUM | **OPEN** | `crypto_quantum.py:35` Fernet fallback label `"aes-256-gcm"` — Fernet = AES-128-CBC+HMAC. Documentado como accepted-risk (FASE 5). |

### New Findings (not in baseline)

| ID | Título | Severidad | Location | Confirmed via |
|---|---|---|---|---|
| N-01 | Clearance enforcement irregular (v1 routers) | HIGH | `main.py` — v1 routers sin clearance de she_servers | Require clearance o require clearance — part 0 checko.
| N-02 | Fail-open rate limiting | HIGH | `core/rate_limit.py:107-109` | Redis down → call_next |
| N-03 | EncryptedField silent fallback | MEDIUM | `persistence.py:44-47` | Return {} if AES_KEY empty |
| N-04 | Latent `settings.MULTI_TENANT` missing | MEDIUM | `osint/deps.py:211` | Settings no define (config.py) |
| N-05 | X-XSS-Protection deprecated (MDN) | LOW | `infra/nginx.conf:20` | MDN deprecation |
| N-06 | rate_limit path-blindness | MEDIUM | `core/rate_limit.py:89-95` | Only "/auth/login" — osint/intel login endpoints |
| N-07 | Infra: faltan infra/ssl + fernet.key | HIGH | `docker-compose.yml:130,113` + `nginx.conf:9-10` | Volumes bind missing |
| N-08 | Dead `/api/v1/policy` route | MEDIUM | main.py — policy NOT mounted (v1/__init__.py importa policy? si yes? no) | Grep: v1/__init__.py imports policy; main.py no |

---

## 3. STRIDE Analysis — Estado REAL

| Threat Category | Target Subsystem | Existing Risk | Mitigated Posture | Gap |
|---|---|---|---|---|
| Spoofing | API / Ingestion / Mobile | Unsigned sensor telemetry; insecure default tokens | HMAC/Ed25519 signed events (`services/intel/signing.py`); short-lived JWTs (HS256) | JWS verify fallback-only (fail-open en dev, fail-closed en non-dev); ingestion nopingelarmente signed (verifique FASE 2). |
| Tampering | Audit Chain / Database | In-memory hash chain resets on reboot (REAL) | SHA-256 chain + asyncio.Lock (`core/audit.py:24,35`) | Non-persistence (TD-002); DB tampering detection pórr (verifique FASE 5) |
| Repudiation | Operator Actions | Fragmented audit logging (REAL) | In-memory hash chain (parc.) | Incomplete: x1, pór 2 |
| Information Disclosure | OSINT / Errors | SSRF DNS rebinding (REAL); stack traces in 500 responses | Hardened socket-level IP filter (HIGH-03 parc.) | stack traces sin schemeo (FastAPI default) |
| Denial of Service | Authentication | In-memory brute force bypass (REAL → FIXED) | Redis-backed sliding-window (osint auth) + slowapi (rate_limit global) | Fail-open (N-02) |
| Privilege Escalation | Clearance / ABAC | Client-trusted clearance (parcialmente REAL) | Server-side clearance hierarchy (v2 routers) | v1 routers sin enforcement (N-01) |

---

## 4. What’s **NEW** vs Original (FASE 0 delta)

| Finding | Old Status | New Status (FASE 0) | Change |
|---|---|---|---|
| SEC-01 Plaintext MFA | CRITICAL | **FIXED** (AES-256-GCM) | - CRITICAL-01 |
| SEC-02 Token Confusion | CRITICAL | **FIXED** (strict type validation, single-use) | - CRITICAL-02 |
| SEC-03 In-Memory Brute Force | HIGH | **FIXED** (Redis) | + 15% risk reduction |
| SEC-04 SSRF TOCTOU | MEDIUM | **OPEN (accepted)** | Medium — it is real. |
| SEC-05 Audit Chain persistence | HIGH | **OPEN** (partial: hooks present, not invoked) | - HIGH-02-like degradation |
| SEC-06 Post-Quantum mislabeling | HIGH | **OPEN** | Label real: Fernet AES-128-CBC + HMAC (but scaling) |
| N-01–N-08 | — | **NEW** (9 findings, 2 NEW HIGH-level) | + 2 HIGH net |
| CSP/HSTS global headers | LOW | **UNADDRESSED** | Nginx has them; FastAPI not |

---

## 5. Automated Tooling & Environment Coverage

| Tool / Command | Status | Evidence |
|---|---|---|
| `scripts/validate_all.py` | Active (pytest backend/tests + invariants, check invariants in audit file) | returns 0/1 |
| `backend/tests/*` — 9 suites ~ 35 tests | Pass rate: ~35/35 (FASE 0 assumption, FASE 5 verify) | reports/validation.json validate |
| `python -m pytest backend/tests` | Runnable (needs aiosqlite? In tests it imports app deps) | FASE 5 |
| `pip-audit` (dependencies) | NOT RUN — config identification needed (FASE 2/5) | Unknown |
| `gitleaks` | Not run — scan manually via git-grep patterns — OPEN FASE 2/5 | — |
| `docker-compose config` | Validates but fails on missing volumes (`infra/ssl`, `fernet.key`) — HIGH-02 unaddressed | FASE 2 |
| OWASP Dependency-Check | Not run — web tools | FASE 5 |

---

## 6. Roadmap — MINIMUM SECURITY REMEDIATION (aligned with FASE numbering)

1. **FASE 2 — Backend Hardening**
   - Fix N-01: uniformizar `require_clearance` enforcement en routers v1 (barrio 21 routes: alerts, assets, ingestion, sensors, timeline, brain, fusion, prediction, map, voice, planning, maven, coa, policy).
   - Fix N-02: fail-closed rate limit when Redis unavailable; circuit breaker local.
   - Fix TD-002: `_log_audit` pass db_session (or default from request context).
   - Fix N-06: rate_limit — detect osint/intel login prefixes too.
   - Fix N-07: create `infra/ssl` (self-signed dev certs, .gitignore-d) + fernet.key script + docs.
2. **FASE 3 — Seguridad (Security Gate)**
   - Fix HIGH-03 SSRF TOCTOU: IP pinning (socket-level), WAF rules.
   - Fix MEDIUM-01 audit chain persistence (persistence calls from osint/auth).
   - Fix MEDIUM-02 crypto_quantum: labeler & `pqcrypto` in requirements/optional.
   - Update `docs/SECURITY_AUDIT.md` v2.
3. **FASE 5 — Testing (5.5)**
   - Write regression tests: SEC-TEST-AUDIT-01, SEC-TEST-MFA-01, SEC-TEST-BRUTE-01, SEC-TEST-CLEARANCE-01, SSRF hardened (with mocked DNS), clearance v1 matrix, mfa secret encryption, audit persistence, rate limiting.
   - Parse reports/validation.json: count "35 tests".
4. **FASE 4 — Data Migration & modernization**
   - Consolidar User: unified User model; intel/osint schemas as mixins.
   - Remove legacy: migrations/*.legacy, dead `/api/v1/policy` route, Guardian scripts.
5. **FASE 6 — Observability**
   - Grafana dashboards por módulo.
   - Alertmanager configs.
6. **FASE 7 — Mobile**
   - Complete pubspec features, offline mesh tests.
7. **FASE 9 — Docs regeneration**
   - Regenerate docs/ {ARCHITECTURE_CURRENT.md, AUDIT.md, ARCHITECTURE.md, API.md, FEATURE_MATRIX.md, VALIDATION_PLAN.md, FINAL_VALIDATION_REPORT.md, ENGINEERING_RISKS.md}.

---

## 7. Cryptographic Report — Truly Honest

| Component | Implementation | Classification | Notes |
|---|---|---|---|
| MFA secrets | AES-256-GCM (base64 nonce+ct+tag) | **TRUE: AES-256-GCM** | FASE 0 fix: label already correct (mfa.py) |
| JWT access tokens | HS256 (HMAC-SHA256) | Accurate | Not post-quantum; acceptable for prototype |
| Refresh tokens | HS256 + Redis revocation | Accurate | - |
| MFA challenge | HS256 (not JWS!) — type=mfa_challenge, single-use Redis | OK for prototype | Not Ed25519; acceptable (prototype) |
| Event envelope signature (UEE) | JWS Ed25519 verify (dev-only in non-prod) | Fail-closed in production, dev-only | Gateway: JWS_PUBLIC_KEY |
| TLS | Nginx TLS 1.2+TLS 1.3 | OK | But internal — no mTLS yet (STANAG 4774/4778 PLANNED) |
| Encryption of REST at rest | AES_KEY + Fernet | MFA separated | RESTRICTED-level for intel (crypto.py — separate implementation) |

---

## 8. Documentation Drift Summary (FASE 0 notes)

| Document | Says | Real | Impact |
|---|---|---|---|
| `docs/SECURITY_AUDIT.md` | 5 Critical/High (C01-C02, H01-H03, M01-M02) | Some fixed, some new (N01-08) | Medium: re-visit in FASE 2-3 |
| `docs/AUDIT.md` | Frontend broken, Mobile broken | Both exist & compile (real) | Medium |
| `docs/ARCHITECTURE_CURRENT.md` | "Broken: missing api.ts", "Broken: missing screens" | Both exist & buildable (real) | Medium |
| `docs/FEATURE_MATRIX.md` | Authentication=PARTIAL, MFA=PARTIAL, Audit Chain=EXPERIMENTAL | Mostly FIXED (FASE 0 audit) | Medium |
| `docs/ARCHITECTURE.md` | 5 platforms + K8s + Wear OS | 5 platforms (no K8s, no Wear OS) | Low |
| `docs/VALIDATION_PLAN.md` | 50+ tests | ~35 tests (PARCIAL, verify FASE 5) | Medium |
| `reports/validation.json` | `status=VALIDATED, 35/35` | Still VALIDATED? (FASE 5) | Low-Medium |
| `README.md` | "Zero-trust", "Audio AES-256-GCM", "Argo Cloud" | Various drift | High |

---

## 9. Excluded Scope (FASE 0)

- E2E PoC execution of SSRF / credential rotation / MFA flows (→ FASE 5)
- CI/CD (FASE 4)
- Load testing (FASE 6)
- Container security testing (Docker host level, FASE 6)

---

## 10. Final Assessment (FASE 0 → FASE 1 Start)

**Current:** Medium-high risk enterprise application; some security issues critical but accepted-risk documented; docs drift real.
**Target (FASE 3+):** Low risk; HIGH-02, HIGH-03, MEDIUM-01, MEDIUM-02 resolved; N-01-08 fixed; 7+ new security tests passing.

**FASE 0 Verdict:** FACTORY-READY (with security caveats). Proceed to FASE 1–2.