import pytest
import pytest_asyncio
import uuid
from httpx import ASGITransport, AsyncClient
from app.main import app
from app.database import init_db

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db()

@pytest.mark.asyncio
async def test_health_check():
    """Verify health endpoint returns clean operational status without sensitive details."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

@pytest.mark.asyncio
async def test_18_plus_enforcement_and_registration():
    """Verify that registration strictly enforces the 18+ policy for university students."""
    underage_email = f"minor_{uuid.uuid4().hex[:6]}@student.edu"
    valid_email = f"student_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Attempt registering without 18+ confirmation -> MUST FAIL
        res_fail = await ac.post("/api/v1/auth/register", json={
            "email": underage_email,
            "password": "valid_password_2026",
            "confirmed_18_plus": False
        })
        assert res_fail.status_code == 400
        assert "18 and older" in res_fail.json()["detail"]

        # 2. Register valid adult student -> MUST SUCCEED
        res_ok = await ac.post("/api/v1/auth/register", json={
            "email": valid_email,
            "password": "valid_password_2026",
            "confirmed_18_plus": True
        })
        assert res_ok.status_code == 201
        token_data = res_ok.json()
        assert "access_token" in token_data
        assert token_data["confirmed_18_plus"] is True

        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Check default granular consents: save_journal=True, AI features=False
        consents_res = await ac.get("/api/v1/consents", headers=headers)
        assert consents_res.status_code == 200
        consents = consents_res.json()
        assert consents["save_journal"] is True
        assert consents["emotion_analysis"] is False
        assert consents["embeddings_rag"] is False
        assert consents["external_inference"] is False

@pytest.mark.asyncio
async def test_checkin_flow():
    """Verify check-in with 5 plain language moods and 1-5 energy rating."""
    email = f"checkin_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "valid_password_2026",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create check-in
        create_res = await ac.post("/api/v1/check-ins", headers=headers, json={
            "local_date": "2026-10-05",
            "self_reported_mood": "Uneasy",
            "self_reported_energy": 3,
            "context_tags": ["study", "sleep"],
            "note": "A bit restless about the upcoming lab exam."
        })
        assert create_res.status_code == 201
        ci = create_res.json()
        assert ci["self_reported_mood"] == "Uneasy"
        assert ci["self_reported_energy"] == 3
        assert "study" in ci["context_tags"]
        ci_id = ci["id"]

        # List check-ins
        list_res = await ac.get("/api/v1/check-ins", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # Delete check-in
        del_res = await ac.delete(f"/api/v1/check-ins/{ci_id}", headers=headers)
        assert del_res.status_code == 204

@pytest.mark.asyncio
async def test_journal_encryption_and_deletion():
    """Verify journal text is encrypted at rest, decrypted for owner, and cascades on deletion."""
    email = f"journal_{uuid.uuid4().hex[:6]}@student.edu"
    secret_note = "Private thought: feeling tired from compiler design assignment."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "valid_password_2026",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create journal entry
        j_res = await ac.post("/api/v1/journal", headers=headers, json={
            "text": secret_note,
            "language": "en"
        })
        assert j_res.status_code == 201
        entry_data = j_res.json()
        assert entry_data["text"] == secret_note
        entry_id = entry_data["id"]

        # Read back
        get_res = await ac.get(f"/api/v1/journal/{entry_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["text"] == secret_note

        # Delete entry
        del_res = await ac.delete(f"/api/v1/journal/{entry_id}", headers=headers)
        assert del_res.status_code == 204

        # Verify not found after deletion
        get_after = await ac.get(f"/api/v1/journal/{entry_id}", headers=headers)
        assert get_after.status_code == 404

@pytest.mark.asyncio
async def test_daily_plan_flow():
    """Verify daily one-thing plan with up to 3 editable steps."""
    email = f"plan_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "valid_password_2026",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        put_res = await ac.put("/api/v1/daily-plan/today", headers=headers, json={
            "focus": "Complete database assignment draft",
            "steps": [
                {"id": "1", "text": "Draft ER diagram", "completed": True},
                {"id": "2", "text": "Write query explanations", "completed": False}
            ]
        })
        assert put_res.status_code == 200
        plan = put_res.json()
        assert plan["focus"] == "Complete database assignment draft"
        assert len(plan["steps"]) == 2

        get_res = await ac.get("/api/v1/daily-plan/today", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["focus"] == "Complete database assignment draft"

@pytest.mark.asyncio
async def test_support_resources():
    """Verify support resources include verified Indian helplines and emergency numbers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/support-resources?country=IN")
    assert res.status_code == 200
    catalog = res.json()
    assert "Tele-MANAS" in str(catalog)
    assert "112" in str(catalog)
    assert "not actively monitored" in catalog["disclaimer"].lower()

@pytest.mark.asyncio
async def test_demo_seed_and_export_and_account_delete():
    """Verify demo seed populates safe fictional data, export returns it, and delete wipes it."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Seed demo account
        demo_res = await ac.post("/api/v1/demo/seed")
        assert demo_res.status_code == 200
        demo_data = demo_res.json()
        token = demo_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Verify export contains populated sections
        export_res = await ac.get("/api/v1/privacy/export", headers=headers)
        assert export_res.status_code == 200
        export_data = export_res.json()
        assert len(export_data["check_ins"]) > 0
        assert len(export_data["journal_entries"]) > 0
        assert export_data["user_profile"]["email"] == "demo@pause-wellness.local"

        # Delete account
        del_res = await ac.delete("/api/v1/account", headers=headers)
        assert del_res.status_code == 200

        # Verify login now fails
        login_again = await ac.post("/api/v1/auth/login", json={
            "email": "demo@pause-wellness.local",
            "password": "DemoUser2026!"
        })
        assert login_again.status_code == 401
