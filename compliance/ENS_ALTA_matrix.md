# ENS ALTA Compliance Matrix (Reference & Verification)

| Control | Status | Verified Technical Baseline | Notes |
|---------|:------:|-----------------------------|-------|
| **org.organizacion** | `VALIDATED` | Role-based and Attribute-based Access Control (RBAC/ABAC) | Enforced via `ABACEngine` and `require_clearance` dependencies. |
| **op.acceso** | `VALIDATED` | MFA (TOTP with AES-256-GCM encryption) + short-TTL JWTs | Single-use challenge tickets (`type="mfa_challenge"`) with Redis-backed revocation. |
| **op.separacion** | `PARTIAL` | Containerized process separation (Docker network isolation) | **Correction:** MicroVM sandboxing is *not implemented*. Container limits and network boundaries active. |
| **mp.alt** | `VALIDATED` | Append-only SHA-256 hash-chained audit trail | Cryptographic linkage backed by database persistence and concurrency locks. |
| **mp.if** | `PARTIAL` | Software AES-256-GCM authenticated encryption | External Hardware Security Module (HSM) integration is planned for future phases. |
| **op.continuidad** | `EXPERIMENTAL` | Resilient offline mesh protocol & local queue | Prototype tested for disconnected operations. |
