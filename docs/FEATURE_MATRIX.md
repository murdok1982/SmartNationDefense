# FEATURE_MATRIX.md — Reality Matrix & Capability Verification

**Document ID:** MTX-2026-SND-001  
**Date:** 2026-09-25  
**System:** SmartNationDefense / SESIS-FEDERATION  
**Version:** Baseline Pre-Upgrade  

---

## 1. Reality Matrix Taxonomy

Each feature is evaluated against strict empirical criteria:

- **Código:** Functional source code exists in the repository.
- **Integrado:** Feature is actively connected to the runtime flow and data pipeline.
- **Test:** Automated unit/integration tests exist and verify behavior.
- **E2E:** Complete scenario-driven automated end-to-end execution exists.
- **Benchmark:** Documented, reproducible throughput/latency metrics exist.
- **Estado (Strictly constrained taxonomy):**
  - `VALIDATED`: Working code + integrated in pipeline + comprehensive tests + E2E + benchmarks.
  - `IMPLEMENTED`: Working code exists and handles domain logic, but missing full integration or tests.
  - `INTEGRATED`: Working code connected into live system pipeline, but lacks comprehensive test/benchmark evidence.
  - `PARTIAL`: Code exists but incomplete, fractured across competing modules, or containing known regressions.
  - `EXPERIMENTAL`: Heuristic, prototype, or uncalibrated implementation without formal verification.
  - `STUB`: Shell functions, placeholder mocks, or non-functional structural definitions.
  - `PLANNED`: Documented in specifications or architecture without substantive code.
  - `UNSUPPORTED`: Claimed in marketing/README but technically infeasible or absent from code.

---

## 2. Core Reality Matrix

| Feature | Código | Integrado | Test | E2E | Benchmark | Estado | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Authentication** | Yes | Partial | Partial | No | No | `PARTIAL` | Fragmented across 3 distinct `User` models and auth endpoints (`/auth`, `/intel/auth`, `/osint/auth`). |
| **MFA** | Yes | Partial | Partial | No | No | `PARTIAL` | Intel module has TOTP; OSINT module has plaintext secret stub and token type conflation. |
| **ABAC / Clearance** | Yes | Partial | Partial | No | No | `PARTIAL` | `ABACEngine` and `require_clearance` exist; not uniformly applied across all C2/v2 routes. |
| **Audit Chain** | Yes | Partial | No | No | No | `EXPERIMENTAL` | In-memory SHA-256 chain; resets on restart; invalid import of nonexistent `app.db.models.audit`. |
| **JDL Fusion** | Yes | Partial | No | No | No | `EXPERIMENTAL` | Rule-based JSON heuristic (`jdl_fusion.py`); no probabilistic filtering (Kalman/Bayesian). |
| **Computer Vision** | Yes | Partial | No | No | No | `EXPERIMENTAL` | YOLOv8 wrapper; phantom military classes (100–103); drone contour resets background subtractor per frame. |
| **Anomaly Detection** | Yes | Partial | No | No | No | `EXPERIMENTAL` | Isolation Forest wrapper in `ml/`; uncalibrated detection thresholds. |
| **OSINT Tools** | Yes | Yes | Yes | No | No | `INTEGRATED` | Atalaya toolsuite (`web_tools.py`, `dns_tools.py`); tests exist for SSRF; TOCTOU DNS rebinding risk present. |
| **Graph Intelligence** | Yes | Partial | No | No | No | `PARTIAL` | Neo4j client exists; schema models and ingest queries partially implemented; lacks continuous graph sync. |
| **LLM Orchestration** | Yes | Partial | No | No | No | `PARTIAL` | Ollama/OpenRouter router; lacks structured Pydantic schema validation for all agent prompts. |
| **Multi-Agent Architecture** | Yes | Partial | No | No | No | `EXPERIMENTAL` | Agents defined in `api/agents/`; permissions and sandboxing not strictly isolated per agent. |
| **Common Operating Picture (COP)** | Yes | No | No | No | No | `PARTIAL` | Next.js components built; **broken** build due to missing `frontend/src/lib/api.ts`. |
| **Mobile Client** | Yes | No | No | No | No | `STUB` | Flutter app created; **unbuildable** due to missing `lib/features/` directory containing all screens. |
| **Offline Mode & Mesh** | Yes | No | No | No | No | `EXPERIMENTAL` | `mesh_protocol.dart` and `mesh_service.dart` defined; lacks offline sync queue and storage layer. |
| **Event Bus (NATS)** | Yes | Yes | No | No | No | `INTEGRATED` | NATS JetStream publisher/consumer wrapper implemented; lacks DLQ and idempotency keys. |
| **Observability** | Yes | Partial | No | No | No | `PARTIAL` | Prometheus config and basic health endpoints exist; lacks distributed tracing and fine-grained metrics. |
| **Docker Orchestration** | Yes | Yes | No | No | No | `INTEGRATED` | `docker-compose.yml` runs stack; insecure defaults and missing non-root hardening. |
| **CI / CD Pipeline** | No | No | No | No | No | `PLANNED` | No GitHub Actions workflow configured in `.github/workflows`. |
| **Post-Quantum Cryptography** | Yes | No | No | No | No | `UNSUPPORTED` | Deceptive Fernet fallback labeled as AES-256-GCM; `pqcrypto` stubs uninstalled. |
| **MicroVM Sandbox** | No | No | No | No | No | `UNSUPPORTED` | Claimed in `compliance/ENS_ALTA_matrix.md`; zero microVM/Firecracker code exists. |

---

## 3. Subsystem Breakdown & Gap Analysis

### 3.1 Authentication & Clearance
- **Claim:** "Enterprise zero-trust RBAC/ABAC with state-grade MFA."
- **Status:** `PARTIAL`
- **Gap:**
  - In `backend/app/api/osint/auth.py`: `_encrypt_secret(secret)` returns plaintext.
  - Interim ticket issues token with `type="access"` instead of `"mfa_challenge"`.
  - Rate limiting is process-local and lost on worker scale.

### 3.2 Fusion & Decision Support
- **Claim:** "Full JDL Levels 0–4 Data Fusion Engine."
- **Status:** `EXPERIMENTAL`
- **Gap:**
  - Levels 0 through 4 are heuristic regex/condition matches over `situation_rules.json`.
  - No sensor registration, sensor calibration, covariance matrices, or ground-truth evaluation datasets.

### 3.3 Presentation Layer (COP)
- **Claim:** "Unified Web and Mobile Tactical COP."
- **Status:** `PARTIAL` (Web) / `STUB` (Mobile)
- **Gap:**
  - Web: Fails TypeScript compile because `src/lib/api.ts` is missing.
  - Mobile: Fails Flutter analyze/compile because `lib/features/*` screens are missing.

---

## 4. Upgrade Target Milestones

| Capability | Current State | Target State (Post-Upgrade) | Target Verification |
|---|---|---|---|
| Unified Auth & MFA | `PARTIAL` | `VALIDATED` | Unit + integration tests for encrypted TOTP, challenge tokens, Redis brute-force lockout. |
| Secure Audit Chain | `EXPERIMENTAL` | `VALIDATED` | DB-backed persistent hash chaining with concurrency locks and tamper detection tests. |
| Web COP Build & Run | `PARTIAL` | `INTEGRATED` | Successful Next.js build with clean `src/lib/api.ts` client. |
| Mobile COP Build & Run | `STUB` | `INTEGRATED` | Implement missing screens & clean Flutter analysis. |
| OSINT SSRF Hardening | `INTEGRATED` | `VALIDATED` | Complete denylist + socket-level IP validation tests. |
| Automated Test Suite | `PARTIAL` (23 tests) | `VALIDATED` (50+ tests) | Unit, integration, security, and E2E scenario testing. |
