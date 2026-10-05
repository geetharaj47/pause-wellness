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
async def test_cross_tenant_isolation():
    """
    CRITICAL SECURITY CHECK:
    Account A cannot read, update, delete, or export Account B's private entries or check-ins.
    """
    email_a = f"tenant_a_{uuid.uuid4().hex[:6]}@student.edu"
    email_b = f"tenant_b_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register Account A
        res_a = await ac.post("/api/v1/auth/register", json={
            "email": email_a,
            "password": "PasswordA123!",
            "confirmed_18_plus": True
        })
        token_a = res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Register Account B
        res_b = await ac.post("/api/v1/auth/register", json={
            "email": email_b,
            "password": "PasswordB123!",
            "confirmed_18_plus": True
        })
        token_b = res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # Account A creates a private journal entry
        entry_a = await ac.post("/api/v1/journal", headers=headers_a, json={
            "text": "Confidential diary entry belonging exclusively to User A"
        })
        entry_a_id = entry_a.json()["id"]

        # Account A creates a check-in
        checkin_a = await ac.post("/api/v1/check-ins", headers=headers_a, json={
            "local_date": "2026-10-05",
            "self_reported_mood": "Difficult",
            "self_reported_energy": 1,
            "context_tags": ["health"],
            "note": "Private health note of User A"
        })
        checkin_a_id = checkin_a.json()["id"]

        # Account A sets a daily plan
        await ac.put("/api/v1/daily-plan/today", headers=headers_a, json={
            "focus": "User A secret plan",
            "steps": [{"id": "1", "text": "Step A", "completed": True}]
        })

        # ---------------------------------------------
        # ATTACK 1: User B tries to read User A's journal entry
        # ---------------------------------------------
        attack_read = await ac.get(f"/api/v1/journal/{entry_a_id}", headers=headers_b)
        assert attack_read.status_code == 404, "User B was able to view User A's journal!"

        # ---------------------------------------------
        # ATTACK 2: User B tries to update User A's journal entry
        # ---------------------------------------------
        attack_update = await ac.patch(f"/api/v1/journal/{entry_a_id}", headers=headers_b, json={
            "text": "Tampered by User B"
        })
        assert attack_update.status_code == 404, "User B was able to modify User A's journal!"

        # ---------------------------------------------
        # ATTACK 3: User B tries to delete User A's journal entry
        # ---------------------------------------------
        attack_del = await ac.delete(f"/api/v1/journal/{entry_a_id}", headers=headers_b)
        assert attack_del.status_code == 404, "User B was able to delete User A's journal!"

        # Verify User A's entry is still intact
        verify_a = await ac.get(f"/api/v1/journal/{entry_a_id}", headers=headers_a)
        assert verify_a.status_code == 200
        assert "Confidential diary entry" in verify_a.json()["text"]

        # ---------------------------------------------
        # ATTACK 4: User B tries to delete User A's checkin
        # ---------------------------------------------
        attack_checkin_del = await ac.delete(f"/api/v1/check-ins/{checkin_a_id}", headers=headers_b)
        assert attack_checkin_del.status_code == 404, "User B was able to delete User A's checkin!"

        # ---------------------------------------------
        # ATTACK 5: User B lists checkins / journal entries
        # ---------------------------------------------
        b_journals = await ac.get("/api/v1/journal", headers=headers_b)
        assert len(b_journals.json()) == 0, "User B saw entries from another user!"

        b_checkins = await ac.get("/api/v1/check-ins", headers=headers_b)
        assert len(b_checkins.json()) == 0, "User B saw check-ins from another user!"

        # ---------------------------------------------
        # ATTACK 6: User B exports data
        # ---------------------------------------------
        b_export = await ac.get("/api/v1/privacy/export", headers=headers_b)
        export_text = str(b_export.json())
        assert "Confidential diary entry" not in export_text
        assert "Private health note" not in export_text
        assert "User A secret plan" not in export_text
