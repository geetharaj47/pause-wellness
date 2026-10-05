import json
import uuid
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.config import settings
from app.database import get_session
from app.models import (
    User, ConsentRecord, CheckIn, JournalEntry,
    DailyPlan, SavedAction, ActionEvent, AuditEvent
)
from app.security import hash_password, encrypt_journal_text, create_access_token

router = APIRouter(prefix="/api/v1/demo", tags=["Fictional Reviewer Demo"])

DEMO_EMAIL = "demo@pause-wellness.local"
DEMO_PASS = "DemoUser2026!"

class DemoSeedResponse(BaseModel):
    message: str
    email: str
    password: str
    access_token: str
    user_id: uuid.UUID

@router.get("/status")
async def get_demo_status():
    """Check whether demo account seeding is enabled on this instance."""
    return {"enabled": settings.ENABLE_DEMO_ACCOUNT}

@router.post("/seed", response_model=DemoSeedResponse, status_code=status.HTTP_200_OK)
async def seed_demo_account(session: AsyncSession = Depends(get_session)):
    """
    Seed or reset the fictional reviewer demo account with clearly labeled synthetic data.
    Disabled in production by default to protect shared tenant privacy.
    """
    is_prod = settings.ENVIRONMENT.lower() in ("production", "prod")
    if is_prod and not settings.ENABLE_DEMO_ACCOUNT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo account seeding is disabled in production to protect shared tenant privacy and prevent state collisions. Please register your own private account via the Register page."
        )

    now = datetime.utcnow()

    # Find or create demo user
    result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
    user = result.scalars().first()

    if user:
        # Clean previous demo records
        uid = user.id
        await session.execute(delete(JournalEntry).where(JournalEntry.user_id == uid))
        await session.execute(delete(CheckIn).where(CheckIn.user_id == uid))
        await session.execute(delete(DailyPlan).where(DailyPlan.user_id == uid))
        await session.execute(delete(SavedAction).where(SavedAction.user_id == uid))
        await session.execute(delete(ActionEvent).where(ActionEvent.user_id == uid))
        await session.execute(delete(ConsentRecord).where(ConsentRecord.user_id == uid))
    else:
        user = User(
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASS),
            created_at=now - timedelta(days=14),
            locale="en-IN",
            selected_country="IN",
            confirmed_18_plus=True,
            is_demo_account=True
        )
        session.add(user)
        await session.flush()

    # Consents for demo (all enabled so reviewer can evaluate all features)
    consents = [
        ConsentRecord(user_id=user.id, purpose="save_journal", granted=True, granted_at=now - timedelta(days=14)),
        ConsentRecord(user_id=user.id, purpose="emotion_analysis", granted=True, granted_at=now - timedelta(days=14)),
        ConsentRecord(user_id=user.id, purpose="embeddings_rag", granted=True, granted_at=now - timedelta(days=14)),
        ConsentRecord(user_id=user.id, purpose="external_inference", granted=False),
    ]
    for c in consents:
        session.add(c)

    # Synthetic check-ins over the past 5 days
    sample_checkins = [
        ("2026-10-01", "Uneasy", 2, ["study", "sleep"], "Long lab session today. Felt a bit behind on coursework."),
        ("2026-10-02", "Okay", 3, ["study"], "Managed to finish the operating systems assignment draft."),
        ("2026-10-03", "Good", 4, ["relationships", "health"], "Went for a 20-minute evening walk with my flatmate."),
        ("2026-10-04", "Uneasy", 2, ["study", "finances"], "Midterm schedule got posted; feeling some pressure about the revision timetable."),
        (date.today().isoformat(), "Okay", 3, ["study", "sleep"], "Started today with a quiet cup of tea before lecture.")
    ]

    for d_str, mood, energy, tags, note in sample_checkins:
        ci = CheckIn(
            user_id=user.id,
            local_date=d_str,
            self_reported_mood=mood,
            self_reported_energy=energy,
            context_tags=json.dumps(tags),
            note=note,
            created_at=now - timedelta(days=2),
            updated_at=now - timedelta(days=2)
        )
        session.add(ci)

    # Synthetic private journal entries (encrypted at rest)
    sample_journals = [
        ("Oct 01: Lab went for four hours straight. My screen fatigue was intense, and I doubted if I would understand compiler design in time.", "en", timedelta(days=4)),
        ("Oct 03: The short walk in the evening helped clear my head. Reminded myself that breaking the project into micro-steps makes it doable.", "en", timedelta(days=2)),
        ("Oct 04: Looked at the syllabus. There are 5 chapters to cover. Decided to tackle Chapter 2 tomorrow morning rather than worrying late at night.", "en", timedelta(days=1))
    ]

    for text, lang, delta in sample_journals:
        je = JournalEntry(
            user_id=user.id,
            created_at=now - delta,
            updated_at=now - delta,
            encrypted_text=encrypt_journal_text(text),
            language=lang,
            deleted_at=None
        )
        session.add(je)

    # Daily plan
    today_plan = DailyPlan(
        user_id=user.id,
        local_date=date.today().isoformat(),
        focus="Focus calmly on compiler design Chapter 2",
        steps_json=json.dumps([
            {"id": "1", "text": "Review lecture slides for 15 minutes", "completed": True},
            {"id": "2", "text": "Draft answers to 2 practice questions", "completed": False},
            {"id": "3", "text": "Take a 5-minute breathing break", "completed": False}
        ]),
        updated_at=now
    )
    session.add(today_plan)

    # Saved actions & action event
    session.add(SavedAction(user_id=user.id, action_id="box-breathing", created_at=now - timedelta(days=3)))
    session.add(SavedAction(user_id=user.id, action_id="break-it-down", created_at=now - timedelta(days=2)))
    session.add(ActionEvent(
        user_id=user.id,
        action_id="box-breathing",
        local_date="2026-10-03",
        outcome="helped",
        user_feedback="Calmed my pulse before heading into the lab.",
        created_at=now - timedelta(days=2)
    ))

    # Audit event
    session.add(AuditEvent(
        user_id=user.id,
        action="DEMO_SEED_RESET",
        timestamp=now,
        status="SUCCESS",
        client_ip=None
    ))

    await session.commit()
    await session.refresh(user)

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return DemoSeedResponse(
        message="Demo account successfully seeded with safe fictional student reflection data.",
        email=DEMO_EMAIL,
        password=DEMO_PASS,
        access_token=token,
        user_id=user.id
    )
