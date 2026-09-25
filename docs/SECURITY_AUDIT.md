# SECURITY_AUDIT.md — Deep Technical Security Assessment & Vulnerability Analysis

**Document ID:** SEC-2026-SND-001  
**Audit Date:** 2026-09-25  
**Auditor:** Agent 3 (Security Engineer) & Autonomous Engineering Group  
**Target:** SmartNationDefense / SESIS-FEDERATION  
**Overall Threat Level:** HIGH (Pre-remediation Baseline)  

---

## 1. Executive Security Assessment

A rigorous vulnerability and architecture audit was performed against the SmartNationDefense codebase. The audit identified multiple critical vulnerabilities that violate fundamental defense and enterprise security standards.

The system cannot be classified as "Zero-trust", "Military-grade", or "Production-ready" until the findings detailed below are systematically resolved and regression-tested.

---

## 2. Vulnerability Findings & Technical Proof

### 2.1 [CRITICAL-01] Plaintext Storage of MFA/TOTP Secrets
- **Location:** [backend/app/api/osint/auth.py](file:///d:/SmartNationDefense/backend/app/api/osint/auth.py#L189-L190)
- **Vulnerable Code:**
  ```python
  def _encrypt_secret(secret: str) -> str:
      return secret
  ```
- **Analysis:** When an OSINT user enrolls in MFA via `/api/v1/osint/auth/mfa/enable`, the secret is stored in the database in cleartext. Any read access to the database or SQL injection vulnerability exposes all TOTP seeds.
- **Remediation:**
  Use the AES-256-GCM implementation from `app.services.intel.auth.mfa.TOTPService.encrypt_secret()`, backed by `settings.MFA_ENCRYPTION_KEY`. Ensure all existing records are migrated with encrypted payloads.

---

### 2.2 [CRITICAL-02] MFA Challenge Token Type Conflation & Missing Invalidation
- **Location:** [backend/app/api/osint/auth.py](file:///d:/SmartNationDefense/backend/app/api/osint/auth.py#L157-L173), [backend/app/core/security.py](file:///d:/SmartNationDefense/backend/app/core/security.py#L30-L50)
- **Vulnerable Pattern:**
  ```python
  def _issue_mfa_ticket(user_id: str, **kw: object) -> str:
      payload = {
          "sub": user_id,
          "type": "mfa_challenge",
          ...
      }
      return create_access_token(payload)
  ```
  In `create_access_token`, the implementation explicitly sets:
  ```python
  to_encode.update({"type": "access", ...})
  ```
- **Analysis:**
  1. The token type `"mfa_challenge"` is overridden with `"type": "access"`.
  2. Because the token is signed with `SECRET_KEY` and bears `"type": "access"`, an attacker can use this interim MFA challenge ticket directly as an access token against protected endpoints without ever verifying the second factor.
  3. Furthermore, tickets are not marked as single-use in Redis, allowing replay attacks within their 5-minute validity window.
- **Remediation:**
  - Issue tickets with dedicated signing key or unmistakable claim `type="mfa_challenge"`.
  - Validate that `get_current_user` strictly rejects `mfa_challenge` tokens.
  - Store ticket JTI in Redis upon verification to prevent reuse.

---

### 2.3 [HIGH-01] Distributed Brute-Force Bypass (Local In-Memory State)
- **Location:** [backend/app/api/osint/auth.py](file:///d:/SmartNationDefense/backend/app/api/osint/auth.py#L113-L149)
- **Vulnerable Code:**
  ```python
  class _BruteForceProtector:
      def __init__(self):
          self._failures: dict[str, list[tuple[str, float]]] = {}
          self._lockouts: dict[str, float] = {}
  ```
- **Analysis:**
  In-memory tracking provides zero protection in a production deployment where multiple Uvicorn workers or Docker container replicas run behind a load balancer. An attacker can distribute authentication attempts across workers without triggering lockout.
- **Remediation:**
  Implement Redis sliding-window counters with atomic INCR and EXPIRE operations tracking IP and username combinations.

---

### 2.4 [HIGH-02] Insecure Default Credentials & Production Ingestion
- **Location:** `.env.example`, `docker-compose.yml`, `backend/app/core/config.py`
- **Exposed Defaults:**
  - `ADMIN_INITIAL_PASSWORD=admin123`
  - `POSTGRES_PASSWORD=change-me-in-production`
  - `NEO4J_PASSWORD=change-me-in-production`
  - `SECRET_KEY=cambia-esto-en-produccion`
- **Analysis:** If deployed with default environment variables, the system is immediately vulnerable to automated credential stuffing.
- **Remediation:**
  The backend must refuse to start (`sys.exit(1)`) in `ENVIRONMENT=production` if any secret matches default patterns or is missing.

---

### 2.5 [HIGH-03] SSRF TOCTOU (Time-of-Check to Time-of-Use) in OSINT Web Fetch
- **Location:** [backend/app/services/osint/tools/web_tools.py](file:///d:/SmartNationDefense/backend/app/services/osint/tools/web_tools.py#L72-L119)
- **Vulnerability:**
  `is_safe_url_async` resolves DNS to verify whether the target IP is private. However, `httpx.AsyncClient.get()` subsequently resolves the hostname again independently during connection establishment.
- **Exploitation:** An attacker configuring a DNS server that returns a public IP on the first query (validation) and `169.254.169.254` or `127.0.0.1` on the second query (HTTP request) bypasses the SSRF filter completely.
- **Additional Defect:** Missing blocked IP ranges:
  - `0.0.0.0/8`
  - `100.64.0.0/10` (Carrier-grade NAT)
  - `198.18.0.0/15` (Benchmarking)
  - `240.0.0.0/4` (Reserved)
  - `::ffff:0:0/96` (IPv4-mapped IPv6)
- **Remediation:**
  Add comprehensive IP denylist and perform socket-level verification or pinning of the resolved IP address.

---

### 2.6 [MEDIUM-01] Ephemeral & Non-guarded Audit Chain
- **Location:** [backend/app/core/audit.py](file:///d:/SmartNationDefense/backend/app/core/audit.py)
- **Vulnerabilities:**
  1. `self.last_hash` is initialized to `None` and held in-memory only. Process restart breaks chain continuity.
  2. Line 46 imports nonexistent `app.db.models.audit`.
  3. No lock prevents race conditions during concurrent `record()` calls, creating corrupt bifurcated chains.
- **Remediation:**
  Persist `AuditLog` in PostgreSQL. Compute the next hash using the latest persisted hash from the database. Guard execution with an `asyncio.Lock()`.

---

### 2.7 [MEDIUM-02] Deceptive Post-Quantum Cryptography Claims
- **Location:** [backend/app/core/crypto_quantum.py](file:///d:/SmartNationDefense/backend/app/core/crypto_quantum.py)
- **Analysis:**
  `QuantumSafeCrypto` advertises Kyber768 and Dilithium3. In environments where `pqcrypto` is missing (the standard case), it falls back to Fernet but logs and returns:
  `{"key": key.decode(), "algorithm": "aes-256-gcm"}`.
  Fernet is AES-128-CBC + HMAC-SHA256, NOT AES-256-GCM. Deceptive labeling in defense software is an unacceptable compliance failure.
- **Remediation:**
  Label algorithms honestly. Use authenticated AES-256-GCM or explicit Fernet without misleading return dictionaries. Mark post-quantum capabilities as "EXPERIMENTAL / UNAVAILABLE".

---

## 3. Threat Modeling (STRIDE Analysis)

| Threat Category | Target Subsystem | Existing Risk | Mitigated Posture |
|---|---|---|---|
| **Spoofing** | API / Ingestion / Mobile | Unsigned sensor telemetry; insecure default tokens | Enforce HMAC/Ed25519 signing on sensor telemetry; short-lived JWTs |
| **Tampering** | Audit Chain / Database | In-memory hash chain reset on reboot | Persistent database-backed SHA-256 chain with WORM export |
| **Repudiation** | Operator Actions | Fragmented audit logging; unhandled exceptions | Mandatory audit interceptor covering all mutating endpoints |
| **Information Disclosure** | OSINT / Errors | SSRF DNS rebinding; stack traces in 500 responses | Hardened socket-level IP filter; sanitized HTTP error schemas |
| **Denial of Service** | Authentication | In-memory brute force bypass | Redis-backed distributed sliding-window rate limiting |
| **Elevation of Privilege** | Clearance / ABAC | Client-trusted clearance; separate uncoordinated User tables | Server-side enforcement of CLEARANCE hierarchy on every protected route |

---

## 4. Minimum Security Remediation Roadmap

1. **Immediate (Blocker):**
   - Fix `_encrypt_secret()` with AES-256-GCM.
   - Separate MFA challenge token type (`"mfa_challenge"`) and enforce single-use revocation.
   - Fail hard in `Settings` if `ENVIRONMENT=production` and secrets are missing or default.
2. **Intermediate:**
   - Migrate `BruteForceProtector` to Redis.
   - Fix `AuditChain` DB model references, concurrency locking, and persistence.
   - Harden `web_tools.py` SSRF protections with complete IP denylist.
3. **Hardening:**
   - Enforce server-side clearance hierarchy verification across all C2 and tactical routes.
   - Remove false claims from documentation and metadata headers.
