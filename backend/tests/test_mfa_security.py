import pytest
from httpx import AsyncClient
from app.core.security import (
    create_access_token,
    create_mfa_challenge_token,
    decode_mfa_token,
    decode_token,
)
from app.services.intel.auth.mfa import totp_service


class TestMFASecurity:
    def test_mfa_secret_encryption_at_rest(self):
        secret = totp_service.generate_secret()
        encrypted = totp_service.encrypt_secret(secret)
        assert encrypted != secret
        assert len(encrypted) > len(secret)
        decrypted = totp_service.decrypt_secret(encrypted)
        assert decrypted == secret

    def test_mfa_challenge_token_type_isolation(self):
        user_id = "test-user-123"
        challenge_token = create_mfa_challenge_token(user_id)
        
        # Must decode successfully with decode_mfa_token
        mfa_payload = decode_mfa_token(challenge_token)
        assert mfa_payload["sub"] == user_id
        assert mfa_payload["type"] == "mfa_challenge"

        # Must fail when decoded as standard access token
        with pytest.raises(Exception):
            decode_token(challenge_token)

    @pytest.mark.asyncio
    async def test_mfa_challenge_cannot_access_protected_routes(
        self, async_client: AsyncClient
    ):
        user_id = "test-user-456"
        challenge_token = create_mfa_challenge_token(user_id)
        headers = {"Authorization": f"Bearer {challenge_token}"}
        
        # Protected route must reject MFA challenge ticket
        response = await async_client.get("/api/v1/c2/", headers=headers)
        assert response.status_code == 401
