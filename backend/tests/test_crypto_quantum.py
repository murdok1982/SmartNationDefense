# -*- coding: utf-8 -*-
"""AC-21: el fallback cripto debe declarar honestamente su algoritmo real."""

import pytest

from app.core.crypto_quantum import (
    QuantumCryptoUnavailable,
    QuantumSafeCrypto,
    qcrypto,
)


class TestQuantumLabels:
    async def test_fallback_keypair_label_is_honest(self):
        keypair = await qcrypto.generate_keypair()
        assert keypair["algorithm"] == "fernet-aes128-cbc-hmac-sha256"
        assert "key" in keypair

    async def test_fallback_encrypt_decrypt_roundtrip(self):
        keypair = await qcrypto.generate_keypair()
        key = keypair["key"].encode()

        ciphertext = await qcrypto.encrypt(b"secreto-clasificado", key)
        assert ciphertext != b"secreto-clasificado"
        assert await qcrypto.decrypt(ciphertext, key) == b"secreto-clasificado"

    async def test_decrypt_with_wrong_key_raises(self):
        first = await qcrypto.generate_keypair()
        second = await qcrypto.generate_keypair()
        ciphertext = await qcrypto.encrypt(b"dato", first["key"].encode())

        with pytest.raises(Exception):
            await qcrypto.decrypt(ciphertext, second["key"].encode())

    async def test_sign_fails_closed_without_pqcrypto(self):
        with pytest.raises(QuantumCryptoUnavailable, match="dilithium3"):
            await qcrypto.sign(b"dato", b"private-key")

    async def test_verify_fails_closed_without_pqcrypto(self):
        with pytest.raises(QuantumCryptoUnavailable, match="dilithium3"):
            await qcrypto.verify(b"dato", b"signature", b"public-key")

    def test_engine_reports_no_pq_libraries(self):
        engine = QuantumSafeCrypto()
        assert engine._kyber_available is False
        assert engine._dilithium_available is False
