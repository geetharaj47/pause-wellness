import json
import uuid
from datetime import datetime
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.database import get_session
from app.models import (
    User, ConsentRecord, CheckIn, JournalEntry,
    EmotionAnalysis, EntryEmbedding, DailyPlan,
    SavedAction, ActionEvent, AuditEvent
)
from app.auth import get_current_user
from app.security import decrypt_journal_text

router = APIRouter(prefix="/api/v1", tags=["Privacy, Export & Deletion"])

@router.get("/privacy/export")
async def export_my_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Export all user-owned data in machine-readable JSON format."""
    now = datetime.utcnow()

    # Consents
    consents_res = await session.execute(
        select(ConsentRecord).where(ConsentRecord.user_id == current_user.id)
    )
    consents = [
        {
            "purpose": c.purpose,
            "granted": c.granted,
            "policy_version": c.policy_version,
            "granted_at": c.granted_at.isoformat() if c.granted_at else None,
            "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None
        }
        for c in consents_res.scalars().all()
    ]

    # Check-ins
    checkins_res = await session.execute(
        select(CheckIn).where(CheckIn.user_id == current_user.id)
    )
    checkins = []
    for ci in checkins_res.scalars().all():
        try:
            tags = json.loads(ci.context_tags)
        except Exception:
            tags = []
        checkins.append({
            "id": str(ci.id),
            "local_date": ci.local_date,
            "self_reported_mood": ci.self_reported_mood,
            "self_reported_energy": ci.self_reported_energy,
            "context_tags": tags,
            "note": ci.note,
            "created_at": ci.created_at.isoformat()
        })

    # Journal Entries (decrypted for owner export)
    journal_res = await session.execute(
        select(JournalEntry).where(JournalEntry.user_id == current_user.id)
    )
    journal_entries = []
    for entry in journal_res.scalars().all():
        journal_entries.append({
            "id": str(entry.id),
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "text": decrypt_journal_text(entry.encrypted_text),
            "language": entry.language,
            "deleted_at": entry.deleted_at.isoformat() if entry.deleted_at else None
        })

    # Emotion analyses
    analyses_res = await session.execute(
        select(EmotionAnalysis).where(EmotionAnalysis.user_id == current_user.id)
    )
    analyses = []
    for ea in analyses_res.scalars().all():
        try:
            labels = json.loads(ea.labels)
        except Exception:
            labels = []
        analyses.append({
            "id": str(ea.id),
            "entry_id": str(ea.entry_id),
            "model_id": ea.model_id,
            "model_version": ea.model_version,
            "labels": labels,
            "created_at": ea.created_at.isoformat()
        })

    # Daily plans
    plans_res = await session.execute(
        select(DailyPlan).where(DailyPlan.user_id == current_user.id)
    )
    plans = []
    for p in plans_res.scalars().all():
        try:
            steps = json.loads(p.steps_json)
        except Exception:
            steps = []
        plans.append({
            "id": str(p.id),
            "local_date": p.local_date,
            "focus": p.focus,
            "steps": steps,
            "updated_at": p.updated_at.isoformat()
        })

    # Action events & saved actions
    events_res = await session.execute(
        select(ActionEvent).where(ActionEvent.user_id == current_user.id)
    )
    action_events = [
        {
            "id": str(ae.id),
            "action_id": ae.action_id,
            "local_date": ae.local_date,
            "outcome": ae.outcome,
            "feedback": ae.user_feedback,
            "created_at": ae.created_at.isoformat()
        }
        for ae in events_res.scalars().all()
    ]

    saved_res = await session.execute(
        select(SavedAction).where(SavedAction.user_id == current_user.id)
    )
    saved_actions = [sa.action_id for sa in saved_res.scalars().all()]

    # Security audit event for data export
    session.add(AuditEvent(
        user_id=current_user.id,
        action="DATA_EXPORT",
        timestamp=now,
        status="SUCCESS",
        client_ip=request.client.host if request.client else None
    ))
    await session.commit()

    return {
        "export_metadata": {
            "application": "Pause AI Student Wellness Companion",
            "version": "1.0.0",
            "exported_at": now.isoformat(),
            "format": "JSON"
        },
        "user_profile": {
            "id": str(current_user.id),
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "selected_country": current_user.selected_country,
            "confirmed_18_plus": current_user.confirmed_18_plus
        },
        "consents": consents,
        "check_ins": checkins,
        "journal_entries": journal_entries,
        "emotion_analyses": analyses,
        "daily_plans": plans,
        "action_events": action_events,
        "saved_actions": saved_actions
    }

@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Transactionally purge all data belonging to the user.
    Cascade deletes: journal entries, analyses, embeddings, check-ins,
    daily plans, action events, saved actions, and consent records.
    """
    uid = current_user.id
    now = datetime.utcnow()

    # Cascade delete all dependent child records
    await session.execute(delete(EntryEmbedding).where(EntryEmbedding.user_id == uid))
    await session.execute(delete(EmotionAnalysis).where(EmotionAnalysis.user_id == uid))
    await session.execute(delete(JournalEntry).where(JournalEntry.user_id == uid))
    await session.execute(delete(CheckIn).where(CheckIn.user_id == uid))
    await session.execute(delete(DailyPlan).where(DailyPlan.user_id == uid))
    await session.execute(delete(ActionEvent).where(ActionEvent.user_id == uid))
    await session.execute(delete(SavedAction).where(SavedAction.user_id == uid))
    await session.execute(delete(ConsentRecord).where(ConsentRecord.user_id == uid))

    # Log deletion audit event without identifying user_id
    session.add(AuditEvent(
        user_id=None,
        action="ACCOUNT_DELETED",
        timestamp=now,
        status="SUCCESS",
        client_ip=request.client.host if request.client else None
    ))

    # Delete user record
    await session.delete(current_user)
    await session.commit()

    return {
        "status": "success",
        "message": "Your account and all associated reflections, journal entries, and model data have been permanently deleted."
    }
