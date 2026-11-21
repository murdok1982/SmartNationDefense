# -*- coding: utf-8 -*-
"""Cobertura del servicio TOTP/MFA (AC-22)."""

import base64

import pyotp
import pytest

from app.services.intel.auth.mfa import (
    TOTPService,
    generate_recovery_codes,
    totp_service,
)

KEY_HEX = "11" * 32  # 32 bytes → AES-256


class TestRecoveryCodes:
    def test_count_and_format(self):
        codes = generate_recovery_codes(count=5, length=10)
        assert len(codes) == 5
        for code in codes:
            assert len(code) == 11  # 10 chars + guion
            assert code[5] == "-"
            assert all(c.isalnum() for c in code.replace("-", ""))

    def test_codes_are_unique(self):
        codes = generate_recovery_codes(count=20)
        assert len(set(codes)) == 20


class TestTOTP:
    def test_secret_and_provisioning_uri(self):
        secret = TOTPService.generate_secret()
        assert len(secret) >= 32
        uri = TOTPService(issuer="SESIS", encryption_key_hex=KEY_HEX).provisioning_uri(
            "operator@sesis.mil", secret
        )
        assert uri.startswith("otpauth://totp/")
        assert "issuer=SESIS" in uri

    def test_verify_valid_and_invalid_codes(self):
        service = TOTPService(issuer="SESIS", encryption_key_hex=KEY_HEX)
        secret = TOTPService.generate_secret()
        code = pyotp.TOTP(secret).now()

        assert service.verify_code(secret, code) is True
        assert service.verify_code(secret, f" {code} ") is True
        assert service.verify_code(secret, "000000") is False

    def test_verify_malformed_input(self):
        service = TOTPService(issuer="SESIS", encryption_key_hex=KEY_HEX)
        secret = TOTPService.generate_secret()

        assert service.verify_code("", "123456") is False
        assert service.verify_code(secret, "") is False
        assert service.verify_code(secret, "abcdef") is False
        assert service.verify_code(secret, "12345") is False


class TestEncryption:
    def test_roundtrip_with_explicit_key(self):
        service = TOTPService(encryption_key_hex=KEY_HEX)
        secret = TOTPService.generate_secret()

        encrypted = service.encrypt_secret(secret)
        assert encrypted != secret
        assert service.decrypt_secret(encrypted) == secret

    def test_roundtrip_with_dev_fallback_key(self):
        service = TOTPService(encryption_key_hex="")
        secret = TOTPService.generate_secret()

        encrypted = service.encrypt_secret(secret)
        assert service.decrypt_secret(encrypted) == secret

    def test_empty_inputs_rejected(self):
        service = TOTPService(encryption_key_hex=KEY_HEX)
        with pytest.raises(ValueError):
            service.encrypt_secret("")
        with pytest.raises(ValueError):
            service.decrypt_secret("")

    def test_truncated_payload_rejected(self):
        service = TOTPService(encryption_key_hex=KEY_HEX)
        truncated = base64.b64encode(b"short").decode()
        with pytest.raises(RuntimeError, match="truncated"):
            service.decrypt_secret(truncated)

    def test_tampered_payload_rejected(self):
        service = TOTPService(encryption_key_hex=KEY_HEX)
        encrypted = service.encrypt_secret("JBSWY3DPEHPK3PXP")
        raw = bytearray(base64.b64decode(encrypted))
        raw[-1] ^= 0xFF  # rompe el tag GCM
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(RuntimeError, match="authentication failed"):
            service.decrypt_secret(tampered)

    def test_invalid_hex_key_rejected(self):
        service = TOTPService(encryption_key_hex="zz" * 32)
        with pytest.raises(RuntimeError, match="hex-encoded"):
            service.encrypt_secret("secret")

    def test_wrong_key_length_rejected(self):
        service = TOTPService(encryption_key_hex="11" * 16)
        with pytest.raises(RuntimeError, match="32 bytes"):
            service.encrypt_secret("secret")

    def test_production_without_key_fails_closed(self, monkeypatch):
        from app.core.config import settings

        monkeypatch.setattr(settings, "ENVIRONMENT", "production", raising=False)
        service = TOTPService(encryption_key_hex="")
        with pytest.raises(RuntimeError, match="MFA_ENCRYPTION_KEY not configured"):
            service.encrypt_secret("secret")

    def test_singleton_is_configured(self):
        assert isinstance(totp_service, TOTPService)
