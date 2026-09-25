# AUDIT.md — SmartNationDefense / SESIS-FEDERATION

**Document ID:** AUD-2026-SND-001  
**Audit Date:** 2026-09-25  
**Auditor:** Autonomous Multi-Agent Engineering Group (Agents 1-10)  
**Target Repository:** `https://github.com/murdok1982/SmartNationDefense`  
**Classification:** DEFENSE / ENGINEERING AUDIT  
**Status:** COMPLETE — BASELINE PHASE  

---

## 1. Executive Summary

A comprehensive architectural, security, code quality, and integration audit was conducted on the **SmartNationDefense / SESIS-FEDERATION** repository.

The codebase represents an ambitious integration attempt combining multiple subprojects (SESIS C2, AEGIS-IMINT satellite analysis, Atalaya OSINT, SpyManager agents, tactical planning, and military wargaming). However, there is a **critical divergence between claimed capabilities and executable code**:

1. **Broken Compilation & Missing Modules:**
   - **Frontend:** Missing `frontend/src/lib/api.ts` prevents Next.js compilation, as `auth-store.ts`, `cop-store.ts`, and `maven-store.ts` all import from `@/lib/api`.
   - **Mobile:** `mobile/sesis_cop/lib/main.dart` imports non-existent screens from `features/` (`login_screen.dart`, `cop_screen.dart`, `intel_feed_screen.dart`, `mission_screen.dart`, `agents_screen.dart`, `satellite_screen.dart`, `duress_screen.dart`). The `mobile/sesis_cop/lib/features` directory was completely omitted from the repository, rendering the mobile application unbuildable.
   - **Backend Model Collisions:** Three distinct models define `__tablename__ = "users"` (`app.db.models.persistence.User`, `app.db.models.intel.user.User`, `app.db.models.osint.user.User`), which will collide in shared database sessions or Alembic migrations.

2. **Severe Security Flaws:**
   - **MFA Secret in Plaintext:** `backend/app/api/osint/auth.py` line 189 implements `def _encrypt_secret(secret: str) -> str: return secret`.
   - **MFA Ticket Conflation:** MFA challenge tokens in `osint/auth.py` are issued using `create_access_token`, which forcibly overrides token type to `"access"`.
   - **In-Memory Rate Limiting & Brute Force:** `BruteForceProtector` and `AuditChain` store state in local Python dicts/variables. In multi-worker or multi-container deployments, rate limiting and lockout protections are trivially bypassed, and audit chains reset on container restarts.
   - **Insecure Defaults:** Default passwords (`admin123`, `change-me-in-production`, `sesis`) are pervasive across `.env.example`, `docker-compose.yml`, and `init_db.py`.
   - **SSRF TOCTOU in OSINT:** `web_tools.py` performs DNS resolution check in `is_safe_url_async`, but `httpx.AsyncClient` subsequently performs its own independent DNS resolution during `safe_http_get`, opening a DNS rebinding window.

3. **False Claims & Phantom Features:**
   - The repository claims "Producción", "Military-grade", "Quantum-safe", "JDL 5 niveles", "MicroVM sandbox", and "Zero-trust".
   - In reality:
     - `crypto_quantum.py` relies on Fernet (AES-CBC + HMAC) and provides placeholder stubs for Kyber/Dilithium.
     - `ml/vision.py` maps non-existent COCO classes (100: "tank", 101: "apc", 102: "artillery", 103: "radar") against a standard YOLOv8 nano model that only predicts classes 0-79.
     - `compliance/ENS_ALTA_matrix.md` asserts "MicroVM sandbox" status is "✅", but no virtualization or microVM isolation exists in the codebase.
     - `compliance/STANAG_4774_4778.md` is a 14-line stub without protocol compliance engines.
     - `scripts/seed_data.py` is a 4-line stub containing only a placeholder print statement.
     - `guardian/` contains disconnected branding/copyright scripts across 6 languages that are never imported or invoked by the application.

4. **Testing Baseline:**
   - The test suite contains only 23 tests in `backend/tests`, achieving superficial passes while completely skipping core end-to-end intelligence pipelines, JDL fusion, case management, computer vision pipelines, and multi-agent coordination.

---

## 2. Codebase Topology & Component Inventory

| Directory / File | Type | Functional Reality | Defect / Risk |
|---|---|---|---|
| `backend/app/main.py` | FastAPI App | Mounts ~20 sub-routers under `/api/v1`, `/api/v2` | Router fragmentation; multiple authentication paradigms |
| `backend/app/core/security.py` | Security Core | JWT issuance, verification, password hashing | Lacks Redis-backed MFA challenge flow and dynamic clearance policy |
| `backend/app/core/config.py` | Settings | Pydantic Settings reading `.env` | Allows insecure defaults in non-production; missing enforcement of strict prod secrets |
| `backend/app/core/audit.py` | Audit Service | In-memory SHA-256 hash chaining | Lost on restart; missing concurrency locks; invalid import `app.db.models.audit` |
| `backend/app/core/crypto_quantum.py` | Crypto Module | Fernet wrapper with `pqcrypto` stub | Claims quantum-safety; misidentifies Fernet as AES-256-GCM |
| `backend/app/api/auth.py` | API Router | Basic login/register for `persistence.User` | Does not support MFA |
| `backend/app/api/intel/auth.py` | API Router | High-grade TOTP MFA & recovery codes | Separate user table (`intel_users`) |
| `backend/app/api/osint/auth.py` | API Router | OSINT login/MFA router | Plaintext MFA secret; in-memory lockout; separate user table |
| `backend/app/services/fusion/` | JDL Engine | Rule-based heuristics for levels 0-4 | Experimental heuristics; not calibrated with ground-truth radar/optical datasets |
| `backend/app/services/vision/` | Computer Vision | Drone contour detector & YOLO wrapper | Otsu thresholding in drone processor resets background model on every frame |
| `ml/vision.py` | Standalone ML | YOLOv8 COCO wrapper | References phantom class IDs 100-103 |
| `ml/anomalies.py`, `correlation.py` | ML Heuristics | Rule-based anomaly checks | Uncalibrated thresholds; lacks statistical validation |
| `frontend/` | Next.js 14 Web App | COP and Dashboard UI | **BROKEN:** Missing `src/lib/api.ts` causes compilation failure |
| `mobile/sesis_cop/` | Flutter App | Mobile client | **BROKEN:** Missing `lib/features/` directory causes compilation failure |
| `guardian/` | Standalone Scripts | Copyright/branding scripts | Dead code; disconnected from core system |
| `compliance/` | Documentation | Regulatory matrices | Stubs claiming non-existent MicroVM and STANAG binding |
| `scripts/seed_data.py` | Utility Script | Seed data script | 4-line stub placeholder |
| `docker-compose.yml` | Orchestration | Multi-container setup | Exposes insecure defaults and missing network segregation |

---

## 3. Detailed Audit by Module

### 3.1 Backend: Authentication & Authorization Fragmentation
There is no single source of truth for identity in the system:
1. **Model Fragmentation:**
   - [backend/app/db/models/persistence.py](file:///d:/SmartNationDefense/backend/app/db/models/persistence.py#L297) declares `User` with columns `username, email, hashed_password, role, classification_level`.
   - [backend/app/db/models/intel/user.py](file:///d:/SmartNationDefense/backend/app/db/models/intel/user.py#L19) declares `User` with columns `email, hashed_password, full_name, clearance, tenant_id`.
   - [backend/app/db/models/osint/user.py](file:///d:/SmartNationDefense/backend/app/db/models/osint/user.py#L11) declares `User` with `mfa_enabled, mfa_secret, scopes`.
2. **Endpoints Fragmentation:**
   - `/api/v1/auth/login`: Uses `persistence.User`. No MFA.
   - `/api/v1/intel/auth/login`: Uses `intel.user.User`. State-grade MFA challenge.
   - `/api/v1/osint/auth/login`: Uses `osint.user.User`. Plaintext secret MFA stub.

### 3.2 Backend: Audit Trail Integrity
[backend/app/core/audit.py](file:///d:/SmartNationDefense/backend/app/core/audit.py) implements `AuditChain`:
- `self.last_hash` is initialized to `None` in memory.
- If the application crashes or restarts, the hash chain starts again from the genesis hash (`"0000...0000"`).
- Line 46 attempts: `from app.db.models.audit import AuditLog`. This module **does not exist**, meaning executing `audit_chain.record(..., db_session=session)` throws an unhandled `ImportError`.
- No async lock guards `record()`, leading to race conditions under concurrent requests.

### 3.3 Backend: Computer Vision & Sensor Fusion
- [backend/app/services/vision/drone_processor.py](file:///d:/SmartNationDefense/backend/app/services/vision/drone_processor.py):
  In `_compute_heatmap`, `cv2.createBackgroundSubtractorMOG2()` is instantiated anew inside the per-frame method, discarding temporal history and defeating the background subtractor.
- [backend/app/services/fusion/jdl_fusion.py](file:///d:/SmartNationDefense/backend/app/services/fusion/jdl_fusion.py):
  Contains a complete Python data structure modeling JDL Levels 0 through 4, but operates entirely on static JSON rule matching (`situation_rules.json`). There is no Kalman filtering, Bayesian network, or Dempster-Shafer evidential reasoning.

### 3.4 Frontend Audit
- [frontend/src/store/auth-store.ts](file:///d:/SmartNationDefense/frontend/src/store/auth-store.ts), [cop-store.ts](file:///d:/SmartNationDefense/frontend/src/store/cop-store.ts), and [maven-store.ts](file:///d:/SmartNationDefense/frontend/src/store/maven-store.ts) import `apiFetch`, `apiLogin`, `clearTokens` from `@/lib/api`.
- [frontend/src/lib](file:///d:/SmartNationDefense/frontend/src/lib) contains ONLY `cop-types.ts`.
- Consequently, executing `npm run build` or `npm run dev` fails immediately with module resolution errors.

### 3.5 Mobile Audit
- [mobile/sesis_cop/lib/main.dart](file:///d:/SmartNationDefense/mobile/sesis_cop/lib/main.dart) imports:
  - `features/auth/screens/login_screen.dart`
  - `features/dashboard/screens/cop_screen.dart`
  - `features/intel/screens/intel_feed_screen.dart`
  - `features/c2/screens/mission_screen.dart`
  - `features/agents/screens/agents_screen.dart`
  - `features/satellite/screens/satellite_screen.dart`
  - `features/auth/screens/duress_screen.dart`
- None of these files or directories exist in `mobile/sesis_cop/lib/features/`.
- Flutter static analysis and compilation fail 100%.

### 3.6 Machine Learning & Rules
- [ml/vision.py](file:///d:/SmartNationDefense/ml/vision.py): Lines 24-25 declare class IDs 100 ("tank"), 101 ("apc"), 102 ("artillery"), 103 ("radar"). Standard YOLOv8 trained on MS-COCO only has 80 classes (indices 0 to 79). Detections of tanks and artillery using this model will never trigger.

---

## 4. Remediation Directives (Priority Order)

1. **Security & Auth Consolidation:** Unify user identity, fix `_encrypt_secret` with AES-256-GCM, isolate MFA challenge tokens (`type="mfa_challenge"`), implement Redis distributed brute-force protection, eliminate default passwords in production.
2. **Frontend & Mobile Restorations:** Implement `frontend/src/lib/api.ts` with robust token management, and build compliant screen stubs and offline data synchronization in `mobile/sesis_cop`.
3. **Audit Trail Hardening:** Persist `AuditChain` state, eliminate invalid imports, add concurrency locking, and integrate database persistence.
4. **Data Model & Provenance:** Add strict Pydantic schemas, provenance metadata (`source_id`, `model_id`, `model_version`, `confidence`, `human_review`), and explicit classification checking.
5. **Elimination of False Claims:** Refactor README, compliance documents, and API specifications to reflect realistic engineering terms (Prototype, Reference Implementation, Experimental, Tested).
