import pytest
import pytest_asyncio
import uuid
from httpx import ASGITransport, AsyncClient
from sqlmodel import select
from app.main import app
from app.database import init_db, get_session
from app.models import AuditEvent
from app.services.crisis_service import crisis_service

@pytest_asyncio.fixture(scope="module", autouse=True)
async def setup_database():
    await init_db()

@pytest.mark.asyncio
async def test_crisis_explicit_urgent_detection():
    """Verify high-urgency immediate crisis expressions."""
    explicit_examples = [
        "I can't take this anymore, I want to kill myself tonight.",
        "Planning to end my life after exams.",
        "Going to commit suicide, goodbye everyone."
    ]

    for text in explicit_examples:
        res = crisis_service.evaluate_text(text)
        assert res.detected_class == "explicit_urgent_language"
        assert res.support_action == "urgent_modal"
        assert res.confidence_label == "high"
        assert len(res.helpline_contacts) >= 2
        # Check that Tele-MANAS is included
        assert any("Tele-MANAS" in c["name"] for c in res.helpline_contacts)

@pytest.mark.asyncio
async def test_crisis_ambiguous_distress_detection():
    """Verify ambiguous deep distress expressions receive optional support banner."""
    ambiguous_examples = [
        "I feel like there is no reason to live anymore.",
        "I just don't want to wake up tomorrow morning.",
        "Everyone would be better off without me here."
    ]

    for text in ambiguous_examples:
        res = crisis_service.evaluate_text(text)
        assert res.detected_class == "ambiguous_distress"
        assert res.support_action == "optional_banner"
        assert res.confidence_label == "moderate"

@pytest.mark.asyncio
async def test_crisis_negation_defense():
    """Verify that negations do not trigger false alarms."""
    negated_examples = [
        "I had a rough day but I do not want to die.",
        "I am definitely not suicidal.",
        "I stopped feeling like I wanted to end my life."
    ]

    for text in negated_examples:
        res = crisis_service.evaluate_text(text)
        assert res.detected_class != "explicit_urgent_language"
        assert res.support_action != "urgent_modal"

@pytest.mark.asyncio
async def test_crisis_idiomatic_student_expressions():
    """Verify common student idioms do not cause false crisis alarms."""
    idioms = [
        "This discrete math homework is killing me!",
        "We were dying of laughter at the hostel movie night.",
        "I am dead tired after spending 5 hours in the physics lab.",
        "Just killing time before the next lecture starts."
    ]

    for text in idioms:
        res = crisis_service.evaluate_text(text)
        assert res.detected_class == "no_signal_detected"
        assert res.support_action == "none"

@pytest.mark.asyncio
async def test_crisis_third_party_concern():
    """Verify third-party concern is flagged as supportive guidance rather than self-crisis."""
    res = crisis_service.evaluate_text("My friend Rohan told me he feels suicidal and I'm scared for him.")
    assert res.detected_class == "ambiguous_distress"
    assert res.is_third_party is True
    assert "someone close to you" in res.user_message.lower()

@pytest.mark.asyncio
async def test_crisis_pauses_emotion_analysis_route():
    """Verify that explicit crisis language halts emotion analysis and displays support UI."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        email = f"crisis_user_{uuid.uuid4().hex[:6]}@student.edu"
        reg = await ac.post("/api/v1/auth/register", json={
            "email": email,
            "password": "ValidPassword2026!",
            "confirmed_18_plus": True
        })
        token = reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Enable emotion analysis consent
        await ac.put("/api/v1/consents", headers=headers, json={"emotion_analysis": True})

        # Create entry with explicit crisis language
        entry_res = await ac.post("/api/v1/journal", headers=headers, json={
            "text": "I can't go on, I plan to kill myself tonight.",
            "language": "en"
        })
        entry_id = entry_res.json()["id"]

        # Request emotion analysis -> MUST PAUSE and return crisis_support
        analysis_res = await ac.post(f"/api/v1/journal/{entry_id}/analyze", headers=headers)
        assert analysis_res.status_code == 200
        data = analysis_res.json()

        assert data["status"] == "crisis_support"
        assert data["abstained"] is True
        assert data["labels"] == []
        assert "human support" in data["user_facing_explanation"].lower() or "overwhelming" in data["user_facing_explanation"].lower()

@pytest.mark.asyncio
async def test_crisis_privacy_no_raw_text_in_audit_logs():
    """STRICT PRIVACY REQUIREMENT: Raw crisis text is never written to audit logs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Check check-safety endpoint
        res = await ac.post("/api/v1/support-resources/check-safety", json={
            "text": "I feel like ending my life"
        })
        assert res.status_code == 200
        assert res.json()["detected_class"] == "explicit_urgent_language"

        # Verify audit_events table does not contain the crisis text
        async for session in get_session():
            events_res = await session.execute(select(AuditEvent))
            events = events_res.scalars().all()
            for ev in events:
                assert "ending my life" not in (ev.action or "")
            break
