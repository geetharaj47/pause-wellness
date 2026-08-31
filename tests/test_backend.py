import pytest
import uuid
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database import init_db

@pytest.mark.asyncio
async def test_health_check():
    """Verify that the health check endpoint is operational and returns healthy status."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        response = await ac.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "environment" in response.json()

@pytest.mark.asyncio
async def test_root():
    """Verify root redirect details."""
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "MindTrace" in response.json()["message"]

@pytest.mark.asyncio
async def test_auth_flows():
    """Verify user registration and authentication validation exceptions."""
    await init_db()
    unique_email = f"test_{uuid.uuid4().hex}@mindtrace.org"
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:

        # Test Registration
        reg_response = await ac.post("/api/auth/register", json={
            "email": unique_email,
            "password": "securepassword123",
            "timezone": "UTC"
        })
        assert reg_response.status_code == 201
        data = reg_response.json()
        assert "access_token" in data
        assert data["email"] == unique_email
        
        # Test Double Registration Error
        dup_response = await ac.post("/api/auth/register", json={
            "email": unique_email,
            "password": "securepassword123",
            "timezone": "UTC"
        })
        assert dup_response.status_code == 400
        
        # Test Login
        login_response = await ac.post("/api/auth/login", json={
            "email": unique_email,
            "password": "securepassword123"
        })
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()

        # Test Wrong Credentials Login
        bad_login_response = await ac.post("/api/auth/login", json={
            "email": unique_email,
            "password": "wrongpassword"
        })
        assert bad_login_response.status_code == 401

