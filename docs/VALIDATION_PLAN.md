# VALIDATION_PLAN.md — Comprehensive Verification, Test Strategy & Benchmark Plan

**Document ID:** VAL-2026-SND-001  
**Date:** 2026-09-25  
**System:** SmartNationDefense / SESIS-FEDERATION  
**Lead Engineer:** Agent 9 (QA / Validation Engineer) & Multi-Agent Engineering Group  

---

## 1. Validation Philosophy & Quality Gates

In accordance with Section 1 of the Master Directive:
```text
AUDIT → UNDERSTAND → BASELINE → DESIGN → IMPLEMENT → INTEGRATE → TEST → SECURITY AUDIT → BENCHMARK → VALIDATE → DOCUMENT → REGRESSION TEST
```

No feature shall be designated as `VALIDATED` without:
1. Executable source code conforming to architecture standards.
2. Verified integration into the active runtime data pipeline.
3. Automated unit and integration test coverage.
4. Passing security regression tests.
5. End-to-end execution evidence.

---

## 2. Test Architecture & Directory Organization

```text
backend/tests/
├── conftest.py                   # Centralized test configuration, fixtures, mocks
├── unit/
│   ├── test_auth_crypto.py       # AES-256-GCM secret encryption, TOTP generation
│   ├── test_mfa_flow.py          # Challenge tokens, single-use, type isolation
│   ├── test_brute_force.py       # Redis-backed rate limiting & sliding-window lockouts
│   ├── test_audit_chain.py       # SHA-256 hash chaining, concurrency, persistence
│   ├── test_jdl_fusion.py        # JDL Levels 0–4 rule processing & heuristics
│   └── test_cv_engine.py         # YOLO loader, bounding boxes, background subtraction
├── integration/
│   ├── test_ingestion_pipeline.py# Sensor telemetry -> NATS -> Fusion -> DB
│   ├── test_case_management.py   # Cases, evidence, reports, entities
│   └── test_llm_orchestrator.py  # Structured Pydantic outputs, fallback provenance
├── security/
│   ├── test_classification_leak.py # Clearance enforcement (OPEN, RESTRICTED, SECRET, TOP_SECRET)
│   ├── test_ssrf_hardened.py     # DNS rebinding, internal IP denylist, IPv6, redirects
│   ├── test_jwt_tampering.py     # Algorithm confusion, forged claims, revoked JTI
│   └── test_audit_immutability.py# Tamper detection, reordered events, inserted events
└── e2e/
    └── test_full_intelligence_cycle.py # Full scenario from login to audit
```

---

## 3. High-Priority Test Specifications

### 3.1 Security Test: MFA Secret Encryption & Challenge Isolation
- **ID:** `SEC-TEST-MFA-01`
- **Objective:** Verify that MFA secrets are never persisted in plaintext, and MFA challenge tickets cannot be used as access tokens.
- **Assertions:**
  1. Setting up MFA stores an AES-256-GCM encrypted string in `User.mfa_secret`.
  2. The interim ticket returned upon initial password verification bears claim `type="mfa_challenge"`.
  3. Attempting to call protected endpoints (`/api/v1/c2/alerts`) with an `mfa_challenge` token returns `HTTP 401 Unauthorized`.
  4. The ticket is single-use: completing verification invalidates the ticket in Redis. Re-verifying with the same ticket fails.

### 3.2 Security Test: Distributed Brute-Force Lockout
- **ID:** `SEC-TEST-BRUTE-01`
- **Objective:** Verify lockout occurs after 5 failed authentication attempts regardless of client rotation across workers.
- **Assertions:**
  1. 5 consecutive failed logins for username `analyst1` trigger `HTTP 429 Too Many Requests`.
  2. The lockout persists for the configured window (300 seconds).
  3. Successful login with correct credentials resets the failure counter.

### 3.3 Security Test: Classification & Clearance Enforcement
- **ID:** `SEC-TEST-CLEARANCE-01`
- **Objective:** Verify server-side clearance hierarchy prevents data leakage.
- **Matrix:**
  - `OPEN` user accessing `OPEN` resource $\rightarrow$ **200 ALLOW**
  - `OPEN` user accessing `SECRET` resource $\rightarrow$ **403 FORBIDDEN**
  - `SECRET` user accessing `OPEN` resource $\rightarrow$ **200 ALLOW**
  - `SECRET` user accessing `TOP_SECRET` resource $\rightarrow$ **403 FORBIDDEN**
  - `TOP_SECRET` user accessing `SECRET` resource $\rightarrow$ **200 ALLOW**

### 3.4 Integration Test: Persistent Audit Chain Integrity
- **ID:** `INT-TEST-AUDIT-01`
- **Objective:** Verify SHA-256 hash chaining remains consistent across simulated restarts and detects tampering.
- **Assertions:**
  1. Record $N$ events: each event's `previous_hash` equals the preceding event's `hash`.
  2. Restart simulation: reloading the audit chain picks up the last committed hash from PostgreSQL.
  3. Tampering test: mutating an entry in the database causes `verify_chain()` to return `False`.

---

## 4. End-to-End Master Scenario (E2E)

**Scenario:** Complete Tactical Intelligence Lifecycle
```text
LOGIN
  ↓
MFA CHALLENGE VERIFY
  ↓
CREATE INVESTIGATION CASE
  ↓
INGEST SENSOR OBSERVATION (Telemetry/Drone)
  ↓
VISION ANALYSIS / DETECTION
  ↓
JDL SENSOR FUSION
  ↓
CROSS-CORRELATION & ANOMALY DETECTION
  ↓
INTELLIGENCE REPORT GENERATION (LLM Structured)
  ↓
HUMAN ANALYST REVIEW & AUTHORIZATION
  ↓
PERSISTENT AUDIT EVENT RECORDING
```

**Automated Implementation:** `tests/e2e/test_full_intelligence_cycle.py` will execute this sequence autonomously in the test harness and verify that every step yields valid, correlated data.

---

## 5. Machine-Readable Validation Report Specification

The validation run must generate `reports/validation.json` following this exact JSON schema:

```json
{
  "commit": "string",
  "timestamp": "ISO-8601 UTC string",
  "build": true,
  "tests": {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "skipped": 0,
    "coverage_percent": 0.0
  },
  "security": {
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "features": {
    "authentication": "VALIDATED",
    "mfa": "VALIDATED",
    "abac": "VALIDATED",
    "audit_chain": "VALIDATED",
    "jdl_fusion": "EXPERIMENTAL",
    "computer_vision": "EXPERIMENTAL",
    "anomaly_detection": "EXPERIMENTAL",
    "osint": "VALIDATED",
    "graph_intelligence": "PARTIAL",
    "llm_orchestration": "PARTIAL",
    "multi_agent": "EXPERIMENTAL",
    "cop_web": "INTEGRATED",
    "cop_mobile": "INTEGRATED",
    "offline_mesh": "EXPERIMENTAL",
    "event_bus": "INTEGRATED",
    "observability": "PARTIAL",
    "docker_hardening": "INTEGRATED",
    "cicd": "PLANNED"
  },
  "status": "PASS"
}
```

---

## 6. Execution Command & Tooling

Validation is orchestrated via a single deterministic script:
```bash
python scripts/validate_all.py
```
or via Makefile target:
```bash
make validate
```
This command runs:
1. Static code analysis & linting (`ruff`, `flake8`).
2. Type checking (`mypy`).
3. Unit, integration, security, and E2E test suites (`pytest`).
4. Machine-readable report generation (`reports/validation.json`).
