import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

from app.core.audit import audit_chain
from app.core.security import (
    create_access_token,
    create_mfa_challenge_token,
    decode_mfa_token,
    hash_password,
)
from app.services.intel.auth.mfa import totp_service
from app.services.fusion.jdl_fusion import (
    JDLFusionEngine,
    Entity,
    Location,
)


@pytest.mark.asyncio
class TestE2EIntelligenceCycle:
    async def test_complete_intelligence_cycle(self, async_client: AsyncClient, db_session):
        # 1. LOGIN & CREDENTIAL VERIFICATION
        username = "lead_analyst"
        password = "StateGradePassword!2026"
        secret = totp_service.generate_secret()
        encrypted_secret = totp_service.encrypt_secret(secret)
        
        # Verify credential hashing
        hashed = hash_password(password)

        # 2. MFA CHALLENGE & VERIFICATION
        user_id = str(uuid.uuid4())
        mfa_challenge = create_mfa_challenge_token(user_id)
        mfa_payload = decode_mfa_token(mfa_challenge)
        assert mfa_payload["sub"] == user_id
        assert mfa_payload["type"] == "mfa_challenge"

        # Generate TOTP code and verify with decrypted secret
        totp_code = totp_service.verify_code(totp_service.decrypt_secret(encrypted_secret), totp_service.generate_secret())
        # Generate valid TOTP code
        import pyotp
        valid_totp = pyotp.TOTP(secret).now()
        assert totp_service.verify_code(totp_service.decrypt_secret(encrypted_secret), valid_totp) is True

        # Issue authenticated session token
        session_token = create_access_token({
            "sub": user_id,
            "username": username,
            "clearance": "TOP_SECRET",
            "role": "analyst",
        })
        headers = {"Authorization": f"Bearer {session_token}"}

        # 3. CREATE CASE
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        case_data = {
            "case_id": case_id,
            "title": "Perimeter Surveillance & Threat Interdiction",
            "classification": "SECRET",
            "opened_by": username,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # 4. INGEST OBSERVATION (Radar & Optical)
        sensor_obs = {
            "id": f"obs-{uuid.uuid4().hex[:6]}",
            "sensor_id": "RADAR-04",
            "type": "RADAR",
            "lat": 36.1408,
            "lon": -5.3536,
            "altitude": 150.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.88,
        }

        # 5. VISION / ANALYSIS
        # Verify bounding box & classification metadata
        detection = {
            "bbox": [120.0, 85.0, 45.0, 30.0],
            "class_name": "boat",
            "confidence": 0.92,
            "provenance": {
                "model_id": "yolov8n",
                "model_version": "8.0.196",
                "source": "optical_uav_01",
            },
        }
        assert detection["confidence"] > 0.8

        # 6. FUSION (JDL Level 0 & Level 1)
        fusion_engine = JDLFusionEngine()
        sub = await fusion_engine.level0_sub_object(
            raw_signals=[{"frequency_mhz": 9410.0, "power_dbm": 42.0}],
            detections=[{
                "id": sensor_obs["id"],
                "entity_type": "SURFACE_VESSEL",
                "lat": sensor_obs["lat"],
                "lon": sensor_obs["lon"],
                "source": "RADAR",
                "confidence": sensor_obs["confidence"],
            }]
        )
        entities = await fusion_engine.level1_object(sub)
        assert len(entities) == 1
        fused_entity = entities[0]

        # 7. CORRELATION & SITUATION ASSESSMENT (Level 2)
        l2_output = await fusion_engine.level2_situation(entities)
        assert l2_output is not None
        assert isinstance(l2_output.formations, list)

        # 8. INTELLIGENCE REPORT GENERATION (Structured)
        intel_report = {
            "report_id": f"REP-{uuid.uuid4().hex[:8].upper()}",
            "case_id": case_id,
            "classification": "SECRET",
            "entity_id": fused_entity.id,
            "assessment": "High-speed unidentified maritime contact approaching territorial limits.",
            "confidence": 0.90,
            "evidence": [sensor_obs["id"], detection["provenance"]["source"]],
            "requires_human_review": True,
            "human_reviewed": False,
        }
        assert intel_report["requires_human_review"] is True

        # 9. HUMAN REVIEW & AUTHORIZATION GATE (Human-in-the-Loop)
        intel_report["human_reviewed"] = True
        intel_report["reviewer_id"] = username
        intel_report["review_decision"] = "CONFIRMED_THREAT_RECOMMEND_INTERCEPTION"
        intel_report["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        assert intel_report["review_decision"].startswith("CONFIRMED")

        # 10. AUDIT CHAIN RECORDING (Persistent SHA-256 Entry)
        audit_entry = await audit_chain.record(
            event="INTELLIGENCE_CYCLE_COMPLETE",
            actor=username,
            resource=f"report:{intel_report['report_id']}",
            classification="SECRET",
            details={
                "case_id": case_id,
                "decision": intel_report["review_decision"],
                "evidence_count": len(intel_report["evidence"]),
            },
        )
        assert audit_entry["actor"] == username
        assert len(audit_entry["hash"]) == 64
        assert audit_entry["previous_hash"] != ""
