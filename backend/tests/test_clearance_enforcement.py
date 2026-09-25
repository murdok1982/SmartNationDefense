import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from app.core.security import require_clearance, CLEARANCE_ORDER


@pytest.mark.asyncio
class TestClearanceEnforcement:
    def _create_mock_request(self, user_clearance: str):
        req = MagicMock()
        req.state.principal = {
            "sub": "test-user",
            "clearance": user_clearance,
            "roles": ["operator"],
        }
        return req

    async def test_open_user_access_open_resource_allowed(self):
        dep = require_clearance("OPEN")
        req = self._create_mock_request("OPEN")
        principal = await dep(req)
        assert principal["clearance"] == "OPEN"

    async def test_open_user_access_secret_resource_denied(self):
        dep = require_clearance("SECRET")
        req = self._create_mock_request("OPEN")
        with pytest.raises(HTTPException) as exc:
            await dep(req)
        assert exc.value.status_code == 403

    async def test_secret_user_access_open_resource_allowed(self):
        dep = require_clearance("OPEN")
        req = self._create_mock_request("SECRET")
        principal = await dep(req)
        assert principal["clearance"] == "SECRET"

    async def test_secret_user_access_top_secret_resource_denied(self):
        dep = require_clearance("TOP_SECRET")
        req = self._create_mock_request("SECRET")
        with pytest.raises(HTTPException) as exc:
            await dep(req)
        assert exc.value.status_code == 403

    async def test_top_secret_user_access_secret_resource_allowed(self):
        dep = require_clearance("SECRET")
        req = self._create_mock_request("TOP_SECRET")
        principal = await dep(req)
        assert principal["clearance"] == "TOP_SECRET"
