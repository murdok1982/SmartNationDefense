# ARCHITECTURE_CURRENT.md — As-Is System Architecture & Defect Mapping

**Document ID:** ARCH-2026-SND-001  
**Date:** 2026-09-25  
**System:** SmartNationDefense / SESIS-FEDERATION  
**Status:** CURRENT STATE (AS-IS AUDIT)  

---

## 1. Architectural Topology Overview

The system is designed as a hybrid microservice and modular monolith federation combining multiple C2/intelligence modules behind a unified FastAPI gateway, with Next.js (Web COP) and Flutter (Mobile COP) frontends.

```mermaid
flowchart TD
    subgraph Clients["Presentation Layer (COP)"]
        WEB["Next.js Web COP (BROKEN: missing api.ts)"]
        MOB["Flutter Mobile (BROKEN: missing screens)"]
    end

    subgraph Gateway["API Gateway / Middleware"]
        FASTAPI["FastAPI App (app/main.py)"]
        AUTH_MID["Auth Middleware & Rate Limiting"]
        CORS["CORS & Trusted Host"]
    end

    subgraph CoreServices["Domain Services (Backend)"]
        AUTH_PERSIST["/api/v1/auth (persistence.User)"]
        AUTH_INTEL["/api/v1/intel/auth (intel.User)"]
        AUTH_OSINT["/api/v1/osint/auth (osint.User)"]
        C2_V1["/api/v1/c2 (Alerts, Ingestion, Sensors)"]
        C2_V2["/api/v2 (Border, Cyber, EW, Space)"]
        SATELLITE["/api/v1/satellite (AEGIS-IMINT)"]
        OSINT["/api/v1/osint (Atalaya Scraping/Tools)"]
        TACTICAL["/api/v1/tactical (OPORD, Wargaming, BDA)"]
        FUSION["JDL Fusion Engine (Rule Heuristics)"]
        VISION["Computer Vision (YOLOv8 + OpenCV Contours)"]
    end

    subgraph DataPlane["Data & Message Infrastructure"]
        PG[("PostgreSQL 16 + pgvector")]
        REDIS[("Redis 7 (Cache, JTI Revocation)")]
        NATS["NATS JetStream (Event Bus)"]
        NEO4J[("Neo4j Graph Database")]
        OLLAMA["Ollama / OpenRouter (LLM)"]
    end

    WEB -.->|Broken Imports| FASTAPI
    MOB -.->|Uncompilable| FASTAPI
    FASTAPI --> AUTH_MID
    AUTH_MID --> CoreServices
    CoreServices --> PG
    CoreServices --> REDIS
    CoreServices --> NATS
    CoreServices --> NEO4J
    CoreServices --> OLLAMA
```

---

## 2. Ingestion & Data Flow Analysis

### 2.1 Sensor Ingestion Path
```mermaid
sequenceDiagram
    autonumber
    participant Sensor as External Sensor / Drone
    participant API as Ingestion API (/api/v1/c2/ingestion)
    participant NATS as NATS Event Bus
    participant Fusion as JDL Fusion Engine
    participant DB as PostgreSQL (Telemetry/Events)
    participant COP as Web COP

    Sensor->>API: POST /ingestion (Observation Payload)
    Note over API: Basic Pydantic validation (No strict cryptographic signature verification)
    API->>DB: INSERT into telemetry / events
    API->>NATS: Publish "sensor.observation"
    NATS->>Fusion: Consume event
    Fusion->>Fusion: Run heuristic rules (situation_rules.json)
    Fusion->>DB: Update track / assessment
    Fusion->>NATS: Publish "fusion.threat_assessment"
    NATS-->>COP: Stream to UI (WebSocket/SSE)
```

**Flaws in current flow:**
1. **Sensor Attribution & Signing:** Sensor inputs are accepted without cryptographic signature or provenance binding. A compromised network path can inject spoofed radar or drone tracks.
2. **Synchronous DB Blocking:** Some ingestion endpoints execute synchronous or non-batched database operations, creating bottlenecks under high telemetry ingest rates.
3. **Missing Backpressure:** NATS message consumption lacks dead-letter queue (DLQ) mechanics and idempotency verification.

---

## 3. Database Schema Overlap & Collision Analysis

A primary architectural flaw is the presence of **three colliding User models** in separate modules targeting the identical table name:

```mermaid
classDiagram
    class PersistenceUser {
        +UUID id
        +String username
        +String email
        +String hashed_password
        +String role
        +String classification_level
        +Boolean is_active
        +DateTime created_at
    }
    class IntelUser {
        +UUID id
        +String email
        +String hashed_password
        +String full_name
        +String clearance
        +String tenant_id
        +Boolean mfa_enabled
        +String mfa_secret (AES-GCM)
    }
    class OsintUser {
        +String id
        +String username
        +String email
        +String hashed_password
        +String scopes
        +String classification
        +Boolean mfa_enabled
        +String mfa_secret (Plaintext)
    }

    PersistenceUser ..> TableUsers : defines __tablename__ = "users"
    IntelUser ..> TableUsers : defines __tablename__ = "users"
    OsintUser ..> TableUsers : defines __tablename__ = "users"
```

### Consequences of Collision:
- Alembic migrations fail or produce conflicting SQL when scanning `metadata`.
- Sessions referencing `User` may query incomplete schemas depending on which submodule was imported first.
- Security privileges, clearances, and MFA secrets are fragmented across three non-interoperable auth routers.

---

## 4. Subsystem Assessment & Divergence Matrix

| Subsystem | Documented Claim | Code Reality | Technical Gap |
|---|---|---|---|
| **Identity & Access** | "MFA-secure Zero-Trust ABAC" | 3 competing auth systems; plaintext MFA secrets in OSINT; in-memory lockout | High: Lack of unified identity, insecure secret storage |
| **Audit Trail** | "Tamper-proof SHA-256 Chain" | In-memory `AuditChain`; resets on restart; invalid import of `app.db.models.audit` | High: Non-persistent audit; untracked tampering |
| **Sensor Fusion** | "Full JDL Levels 0–4 Engine" | Rule-based string matching against `situation_rules.json` | Medium: No probabilistic tracking (Kalman, particle filtering) |
| **Computer Vision** | "Military Vehicle/Threat Detection" | Standard YOLOv8 with invalid classes (100-103); per-frame background subtractor recreation | Medium: Ineffective detection of custom military assets |
| **Web COP** | "Unified Real-Time Dashboard" | Next.js app broken due to missing `lib/api.ts` | Critical: Will not compile or render |
| **Mobile Client** | "Offline-first Secure Mesh Node" | Flutter app missing entire `features/` directory | Critical: Will not compile or launch |
| **Quantum Cryptography**| "Quantum-safe Kyber & Dilithium" | Fernet fallback mislabeled as AES-256-GCM; uninstalled `pqcrypto` stubs | High: Deceptive labeling of symmetric crypto |
| **Simulation / Wargaming** | "Algorithmic COA Generator" | Predefined template expansion; no integration with operational guardrails | Medium: Potential confusion between simulation and operation |

---

## 5. Target Clean Architecture Evolution

To address the audit findings, the architecture must transition from fragmented stubs to a clean layered model:

```mermaid
flowchart TD
    subgraph Presentation["Presentation & Edge"]
        W[Web COP - Next.js 14]
        M[Mobile COP - Flutter Offline-First]
    end

    subgraph EdgeSecurity["API Gateway & Policy Engine"]
        GW[Unified Gateway]
        AUTH[Consolidated Auth Service]
        ABAC[ABAC / Clearance Policy Engine]
        REDIS_RATELIMIT[(Redis Rate Limiter & JTI Blacklist)]
    end

    subgraph CoreEngine["Core Processing & Fusion"]
        INGEST[Sensor & Telemetry Ingestion]
        FUSION_CORE[JDL Fusion Engine - Probabilistic & Heuristic]
        CV_CORE[Vision Engine - YOLOv8 + Safe Image Processing]
        AGENT_ORCH[Multi-Agent Orchestrator - Least Privilege]
    end

    subgraph Decision["Decision Support & Human Review"]
        REC[Recommendation Engine]
        HITL{Human-in-the-Loop Approval}
        AUDIT_SERVICE[Persistent Audit Chain with DB Backing]
    end

    W --> GW
    M --> GW
    GW --> AUTH
    AUTH --> ABAC
    AUTH <--> REDIS_RATELIMIT
    GW --> INGEST
    INGEST --> FUSION_CORE
    INGEST --> CV_CORE
    FUSION_CORE --> AGENT_ORCH
    AGENT_ORCH --> REC
    REC --> HITL
    HITL --> AUDIT_SERVICE
```
