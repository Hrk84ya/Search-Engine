"""Tests for API endpoints (unit-level, mocked DB)."""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    """Health endpoint should return 200 even if DB check is mocked."""
    with patch("app.api.health.get_db") as mock_db:
        mock_session = AsyncMock()
        mock_session.execute = AsyncMock()

        async def fake_get_db():
            yield mock_session

        mock_db.side_effect = fake_get_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"


@pytest.mark.anyio
async def test_auth_token():
    """Auth endpoint should return a token for valid credentials."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/auth/token", json={"username": "admin", "password": "admin"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
