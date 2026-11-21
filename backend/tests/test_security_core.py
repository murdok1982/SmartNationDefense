# -*- coding: utf-8 -*-
"""Cobertura de los primitivos de seguridad (AC-22).

Complementa las suites de integración con pruebas unitarias de:
JWT access/refresh/MFA, revocación de jti, get_current_user, ABAC y
require_clearance. Sin estas ramas, `app/core/security.py` quedaba en 61%.
"""

import time
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core import security
from app.core.security import (
    ABACEngine,
    CLEARANCE_ORDER,
    JWTService,
    create_access_token,
    create_mfa_challenge_token,
    create_refresh_token,
    decode_mfa_token,
    decode_token,
    get_current_user,
    hash_password,
    is_jti_revoked,
    require_clearance,
    revoke_jti,
    verify_password,
)


class SyncRedis:
    """Doble síncrono mínimo para JWTService (setex/get/delete/exists)."""

    def __init__(self):
        self.data: dict = {}

    def setex(self, key, ttl, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)

    def delete(self, key):
        self.data.pop(key, None)

    def exists(self, key):
        return key in self.data


def _request_with(principal):
    request = MagicMock()
    request.state.principal = principal
    return request


class TestPasswordHashing:
    def test_hash_and_verify_roundtrip(self):
        hashed = hash_password("S3cret-Pass!")
        assert hashed != "S3cret-Pass!"
        assert verify_password("S3cret-Pass!", hashed) is True
        assert verify_password("wrong", hashed) is False


class TestAccessTokens:
    def test_create_access_token_from_string_subject(self):
        token = create_access_token("operator-1")
        payload = decode_token(token)
        assert payload["sub"] == "operator-1"
        assert payload["type"] == "access"

    def test_create_access_token_from_dict_with_extra_claims(self):
        token = create_access_token({"sub": "u1"}, clearance="SECRET", roles=["ops"])
        payload = decode_token(token)
        assert payload["clearance"] == "SECRET"
        assert payload["roles"] == ["ops"]

    def test_decode_rejects_wrong_type(self):
        token = create_refresh_token("u1")
        with pytest.raises(HTTPException) as exc:
            decode_token(token)
        assert exc.value.status_code == 401

    def test_decode_accepts_expected_type_override(self):
        token = create_refresh_token("u1")
        payload = decode_token(token, expected_type="refresh")
        assert payload["type"] == "refresh"

    def test_decode_rejects_garbage(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("not-a-jwt")
        assert exc.value.status_code == 401


class TestMfaTokens:
    def test_mfa_roundtrip(self):
        token = create_mfa_challenge_token("u1")
        payload = decode_mfa_token(token)
        assert payload["type"] == "mfa_challenge"

    def test_mfa_rejects_access_token(self):
        with pytest.raises(HTTPException) as exc:
            decode_mfa_token(create_access_token("u1"))
        assert exc.value.status_code == 401

    def test_mfa_rejects_garbage(self):
        with pytest.raises(HTTPException) as exc:
            decode_mfa_token("garbage")
        assert exc.value.status_code == 401

    def test_access_token_cannot_be_mfa_ticket(self):
        with pytest.raises(HTTPException):
            decode_token(create_mfa_challenge_token("u1"))


class TestRevocation:
    async def test_revoke_and_check(self):
        jti = uuid.uuid4().hex
        await revoke_jti(jti, int(time.time()) + 60)
        assert await is_jti_revoked(jti) is True

    async def test_missing_jti_is_not_revoked(self):
        assert await is_jti_revoked(None) is False

    async def test_revoke_without_redis_fails_open(self):
        with patch(
            "app.db.redis_pool.get_redis_pool",
            side_effect=RuntimeError("redis down"),
        ):
            await revoke_jti("jti-x", int(time.time()) + 60)
            assert await is_jti_revoked("jti-x") is False


class TestGetCurrentUser:
    async def test_without_credentials_is_401(self):
        with pytest.raises(HTTPException) as exc:
            await get_current_user(None)
        assert exc.value.status_code == 401

    async def test_accepts_valid_access_token(self):
        token = create_access_token("u1")
        creds = MagicMock()
        creds.credentials = token
        payload = await get_current_user(creds)
        assert payload["sub"] == "u1"

    async def test_rejects_revoked_token(self):
        token = create_access_token("u1")
        creds = MagicMock()
        creds.credentials = token
        with patch("app.core.security.is_jti_revoked", return_value=True):
            with pytest.raises(HTTPException) as exc:
                await get_current_user(creds)
        assert exc.value.status_code == 401

    async def test_rejects_mfa_ticket(self):
        creds = MagicMock()
        creds.credentials = create_mfa_challenge_token("u1")
        with pytest.raises(HTTPException) as exc:
            await get_current_user(creds)
        assert exc.value.status_code == 401


class TestRequireClearance:
    async def test_missing_principal_is_401(self):
        dep = require_clearance("RESTRICTED")
        with pytest.raises(HTTPException) as exc:
            await dep(_request_with(None))
        assert exc.value.status_code == 401

    async def test_insufficient_clearance_is_403(self):
        dep = require_clearance("SECRET")
        with pytest.raises(HTTPException) as exc:
            await dep(_request_with({"clearance": "RESTRICTED"}))
        assert exc.value.status_code == 403

    async def test_sufficient_clearance_returns_principal(self):
        dep = require_clearance("RESTRICTED")
        principal = {"sub": "u1", "clearance": "CONFIDENTIAL"}
        assert await dep(_request_with(principal)) is principal

    def test_clearance_order_is_strict(self):
        ordered = ["OPEN", "RESTRICTED", "CONFIDENTIAL", "SECRET", "TOP_SECRET"]
        assert [CLEARANCE_ORDER[k] for k in ordered] == [0, 1, 2, 3, 4]


class TestABACEngine:
    def test_register_and_allow(self):
        engine = ABACEngine()
        engine.register_policy("intel", "secret")
        assert engine.check_access(_request_with({"clearance": "TOP_SECRET"}), "intel") is True

    def test_denies_low_clearance(self):
        engine = ABACEngine()
        engine.register_policy("intel", "secret")
        with pytest.raises(HTTPException) as exc:
            engine.check_access(_request_with({"clearance": "restricted"}), "intel")
        assert exc.value.status_code == 403

    def test_requires_principal(self):
        engine = ABACEngine()
        with pytest.raises(HTTPException) as exc:
            engine.check_access(_request_with(None), "intel")
        assert exc.value.status_code == 401

    def test_unknown_resource_defaults_public(self):
        engine = ABACEngine()
        assert engine.check_access(_request_with({"clearance": "public"}), "desconocido") is True


class TestJWTService:
    def _service(self, **kwargs):
        return JWTService("service-secret-key-32-chars-minimum-!!!", **kwargs)

    def test_access_token_payload(self):
        svc = self._service()
        payload = svc.decode_token(
            svc.create_access_token("u1", roles=["analyst"], clearance="SECRET", mfa_verified=True)
        )
        assert payload.sub == "u1"
        assert payload.roles == ["analyst"]
        assert payload.clearance == "SECRET"
        assert payload.mfa is True

    def test_expired_access_token_is_401(self):
        svc = self._service()
        token = svc.create_access_token("u1")
        with patch.object(security.jwt, "decode", side_effect=security.JWTError("expired")):
            with pytest.raises(HTTPException) as exc:
                svc.decode_token(token)
        assert exc.value.status_code == 401

    def test_refresh_verify_persists_hash(self):
        svc = self._service()
        redis = SyncRedis()
        token = svc.create_refresh_token("u1", redis_client=redis)

        assert f"refresh:u1" in redis.data
        payload = svc.verify_refresh_token(token, redis_client=redis)
        assert payload.sub == "u1"
        # El refresh es single-use: tras verificar, se revoca el jti y se borra.
        assert f"refresh:u1" not in redis.data

    def test_refresh_without_stored_state_is_rejected(self):
        svc = self._service()
        token = svc.create_refresh_token("u1")
        with pytest.raises(HTTPException) as exc:
            svc.verify_refresh_token(token, redis_client=SyncRedis())
        assert exc.value.status_code == 401

    def test_refresh_type_mismatch_is_400(self):
        svc = self._service()
        with pytest.raises(HTTPException) as exc:
            svc.verify_refresh_token(svc.create_access_token("u1"))
        assert exc.value.status_code == 400

    def test_rotate_tokens_emits_new_pair(self):
        svc = self._service(access_expire_min=5)
        redis = SyncRedis()
        refresh = svc.create_refresh_token("u1", redis_client=redis)
        access, new_refresh = svc.rotate_tokens(
            refresh, redis_client=redis, roles=["ops"], clearance="CONFIDENTIAL"
        )
        assert svc.decode_token(access).clearance == "CONFIDENTIAL"
        assert svc.verify_refresh_token(new_refresh, redis_client=redis).sub == "u1"

    def test_revoke_refresh_token_deletes_state(self):
        svc = self._service()
        redis = SyncRedis()
        svc.create_refresh_token("u1", redis_client=redis)
        svc.revoke_refresh_token("u1", redis_client=redis)
        assert "refresh:u1" not in redis.data

    def test_expire_deltas(self):
        svc = self._service(access_expire_min=1, refresh_expire_days=2)
        assert svc.access_expire == timedelta(minutes=1)
        assert svc.refresh_expire == timedelta(days=2)
