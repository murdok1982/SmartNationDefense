# ENGINEERING_RISKS.md — Comprehensive Risk Register & Impact Assessment

**Document ID:** RSK-2026-SND-001  
**Date:** 2026-09-25  
**System:** SmartNationDefense / SESIS-FEDERATION  
**Classification:** HIGH-RISK ENGINEERING REGISTER  

---

## 1. Risk Evaluation Framework

Risks are categorized across four critical dimensions:
- **Architecture & Maintainability (ARCH)**
- **Security & Integrity (SEC)**
- **Operational Reliability & Resilience (OPS)**
- **Safety, Governance & Compliance (GOV)**

Severity is calculated as `Risk Score = Likelihood (1–5) × Impact (1–5)`.

| Score Range | Classification | Required Action |
|---|---|---|
| **20 – 25** | CRITICAL | Immediate remediation before any deployment or promotion |
| **12 – 19** | HIGH | Remediation required within baseline upgrade cycle |
| **6 – 11** | MEDIUM | Remediation scheduled and monitored |
| **1 – 5** | LOW | Accepted risk or procedural mitigation |

---

## 2. Risk Matrix Overview

```text
       5 │                    SEC-01, ARCH-01
       4 │          SEC-03    SEC-02, ARCH-02, GOV-01
IMPACT 3 │          OPS-02    SEC-04, ARCH-03
       2 │                    OPS-01
       1 │
         └────────────────────────────────────────────
              1       2       3       4       5
                             LIKELIHOOD
```

---

## 3. High & Critical Risk Register

### [CRITICAL] SEC-01: Plaintext MFA Secret Storage in OSINT Module
- **Risk ID:** SEC-01
- **Component:** `backend/app/api/osint/auth.py` (lines 189-190)
- **Description:** `_encrypt_secret(secret: str) -> str: return secret` leaves user 2FA/TOTP seeds stored unencrypted in the database.
- **Likelihood:** 5 | **Impact:** 5 | **Score: 25**
- **Consequence:** Full database dump or unauthorized SQL read exposes all TOTP seeds, completely compromising two-factor authentication.
- **Remediation:** Implement AES-256-GCM encryption with an externally managed key (`MFA_ENCRYPTION_KEY`). Never persist plaintext TOTP secrets.

---

### [CRITICAL] ARCH-01: Unbuildable Frontend and Mobile Codebases
- **Risk ID:** ARCH-01
- **Component:** `frontend/src/` and `mobile/sesis_cop/`
- **Description:**
  - `frontend/src/lib/api.ts` is missing, causing Next.js build failure.
  - `mobile/sesis_cop/lib/features/` is completely absent, causing Flutter build failure.
- **Likelihood:** 5 | **Impact:** 5 | **Score: 25**
- **Consequence:** Complete denial of presentation layer; operators cannot access web or mobile COP.
- **Remediation:** Implement `frontend/src/lib/api.ts` with proper token and error handling. Build clean mock/stub screens and offline services in `mobile/sesis_cop`.

---

### [HIGH] ARCH-02: Database User Table Collisions
- **Risk ID:** ARCH-02
- **Component:** `persistence.py`, `intel/user.py`, `osint/user.py`
- **Description:** Three conflicting SQLAlchemy models all declare `__tablename__ = "users"`.
- **Likelihood:** 4 | **Impact:** 4 | **Score: 16**
- **Consequence:** Migration conflicts, runtime attribute errors, and broken joins when operating in unified sessions.
- **Remediation:** Consolidate onto a unified `User` model with consistent schema, or cleanly namespace table names (`intel_users`, `osint_users`) until identity consolidation is complete.

---

### [HIGH] SEC-02: Ephemeral Audit Trail & Invalid DB Import
- **Risk ID:** SEC-02
- **Component:** `backend/app/core/audit.py`
- **Description:** `AuditChain` stores `last_hash` in memory only. Line 46 imports nonexistent `app.db.models.audit`.
- **Likelihood:** 4 | **Impact:** 4 | **Score: 16**
- **Consequence:** Audit log integrity breaks on every process restart; attempts to persist via DB throw `ImportError`. Repudiation attacks cannot be detected.
- **Remediation:** Store and query the latest hash from persistent storage. Fix the DB model reference to existing audit models (`intel/audit.py` or `persistence.py:AuditLog`). Add concurrency mutex locks.

---

### [HIGH] SEC-03: In-Memory Brute Force Protection Bypass
- **Risk ID:** SEC-03
- **Component:** `backend/app/api/osint/auth.py` (`_BruteForceProtector`)
- **Description:** Lockouts and attempt counters are stored in a process-local Python dictionary.
- **Likelihood:** 3 | **Impact:** 4 | **Score: 12**
- **Consequence:** An attacker rotating requests across multiple Gunicorn/Uvicorn workers or container replicas bypasses the lockout threshold.
- **Remediation:** Move lockout state, progressive delays, and failure counters to Redis with atomic operations.

---

### [HIGH] GOV-01: False & Unsupported Capabilities in Documentation
- **Risk ID:** GOV-01
- **Component:** `README.md`, `compliance/ENS_ALTA_matrix.md`, `compliance/STANAG_4774_4778.md`
- **Description:** Documentation asserts production-readiness, military-grade compliance, MicroVM sandboxing, and quantum-safe cryptography without code backing.
- **Likelihood:** 4 | **Impact:** 4 | **Score: 16**
- **Consequence:** Misrepresentation of system security posture in military/critical environments, leading to catastrophic operational assumptions.
- **Remediation:** Downgrade claims to "prototype", "experimental", "reference implementation", and explicitly document limitations.

---

### [MEDIUM] SEC-04: TOCTOU DNS Rebinding in OSINT Web Tools
- **Risk ID:** SEC-04
- **Component:** `backend/app/services/osint/tools/web_tools.py`
- **Description:** URL validation checks IP safety, but the subsequent HTTP request allows the system resolver to perform a second lookup.
- **Likelihood:** 3 | **Impact:** 3 | **Score: 9**
- **Consequence:** Server-Side Request Forgery (SSRF) to internal cloud metadata (169.254.169.254) or localhost via DNS rebinding.
- **Remediation:** Pin the resolved IP address during connection establishment or implement custom transport adapter that validates resolved IPs at socket connect time.

---

### [MEDIUM] OPS-01: Dead Code and Unused Services
- **Risk ID:** OPS-01
- **Component:** `guardian/` directory (Python, Dart, Rust, Shell, JS, PowerShell)
- **Description:** Standalone copyright scripts execute at import time but are not integrated into any application workflow.
- **Likelihood:** 4 | **Impact:** 2 | **Score: 8**
- **Consequence:** Developer confusion, unnecessary baggage, and accidental stderr pollution.
- **Remediation:** Quarantine or remove auto-execution from `guardian/`.

---

### [MEDIUM] OPS-02: Unvalidated Ingestion Data & Lack of Provenance
- **Risk ID:** OPS-02
- **Component:** `backend/app/api/v1/ingestion.py`
- **Description:** Ingested sensor data lacks provenance metadata (sensor signature, calibration timestamp, confidence bounds).
- **Likelihood:** 3 | **Impact:** 3 | **Score: 9**
- **Consequence:** Corrupted or synthetic data propagates undetected to the COP and decision support tools.
- **Remediation:** Enforce strict Pydantic schemas with mandatory provenance fields (`source_id`, `model_id`, `input_hash`, `timestamp_utc`).
