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
async def test_emotion_consent_gating():
    """Verify emotion analysis strictly gates execution behind user consent."""
    email = f"emotion_user_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Register user (default emotion_analysis consent is False)
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a journal entry
        j_res = await ac.post("/api/v1/journal", headers=headers, json={
            "text": "Stressed with compiler design deadlines and exhausted.",
            "language": "en"
        })
        entry_id = j_res.json()["id"]

        # Attempt to analyze without consent -> MUST FAIL with 403
        analyze_denied = await ac.post(f"/api/v1/journal/{entry_id}/analyze", headers=headers)
        assert analyze_denied.status_code == 403
        assert "explicit consent" in analyze_denied.json()["detail"]

        # Grant emotion analysis consent
        consent_update = await ac.put("/api/v1/consents", headers=headers, json={
            "emotion_analysis": True
        })
        assert consent_update.status_code == 200
        assert consent_update.json()["emotion_analysis"] is True

        # Now analyze -> MUST SUCCEED
        analyze_ok = await ac.post(f"/api/v1/journal/{entry_id}/analyze", headers=headers)
        assert analyze_ok.status_code == 200
        data = analyze_ok.json()
        assert len(data["labels"]) > 0
        assert "confidence_bands" in data
        assert "user_facing_explanation" in data
        assert not any("%" in b for b in data["confidence_bands"]) # No false precision percentage

@pytest.mark.asyncio
async def test_emotion_correction_and_independent_deletion():
    """Verify user can correct/hide analysis and delete it independently of the journal text."""
    email = f"emotion_edit_{uuid.uuid4().hex[:6]}@student.edu"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Enable consent
        await ac.put("/api/v1/consents", headers=headers, json={"emotion_analysis": True})

        # Create entry
        j_res = await ac.post("/api/v1/journal", headers=headers, json={
            "text": "Felt tired from the long lab session today.",
            "language": "en"
        })
        entry_id = j_res.json()["id"]

        # Analyze
        analyze_res = await ac.post(f"/api/v1/journal/{entry_id}/analyze", headers=headers)
        assert analyze_res.status_code == 200

        # User corrects label
        patch_res = await ac.patch(f"/api/v1/journal/{entry_id}/analysis", headers=headers, json={
            "corrected_labels": ["calm/relieved"],
            "user_correction": "Actually I felt quite relieved after the lab."
        })
        assert patch_res.status_code == 200
        patch_data = patch_res.json()
        assert patch_data["labels"] == ["calm/relieved"]
        assert "relieved" in patch_data["user_correction"]

        # Delete analysis independently
        del_analysis = await ac.delete(f"/api/v1/journal/{entry_id}/analysis", headers=headers)
        assert del_analysis.status_code == 204

        # Verify entry still exists intact
        get_entry = await ac.get(f"/api/v1/journal/{entry_id}", headers=headers)
        assert get_entry.status_code == 200
        assert get_entry.json()["emotion_analysis"] is None
        assert "long lab session" in get_entry.json()["text"]
