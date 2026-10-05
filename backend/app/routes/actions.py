import json
import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.database import get_session
from app.models import User, WellnessAction, SavedAction, ActionEvent
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Reviewed Wellness Actions"])

class WellnessActionResponse(BaseModel):
    id: str
    title: str
    steps: List[str]
    duration_minutes: int
    intended_contexts: List[str]
    accessibility_note: str
    source: str
    review_version: str
    is_saved: bool = False
    selection_reason: Optional[str] = None

class SaveActionRequest(BaseModel):
    action_id: str

class ActionEventCreate(BaseModel):
    action_id: str
    local_date: Optional[str] = None
    outcome: str = Field(..., description="'helped', 'about_the_same', 'did_not_try', or 'skipped'")
    user_feedback: Optional[str] = None

class ActionEventResponse(BaseModel):
    id: uuid.UUID
    action_id: str
    local_date: str
    outcome: str
    user_feedback: Optional[str]
    created_at: datetime

VALID_OUTCOMES = {"helped", "about_the_same", "did_not_try", "skipped"}

def _to_action_response(a: WellnessAction, saved_ids: set, context_filter: Optional[str] = None) -> WellnessActionResponse:
    try:
        steps = json.loads(a.steps_json)
    except Exception:
        steps = []
    try:
        contexts = json.loads(a.intended_contexts_json)
    except Exception:
        contexts = []

    reason = None
    if context_filter and context_filter.lower() in contexts:
        reason = f"Shown because you selected '{context_filter.capitalize()}'"
    elif contexts:
        reason = f"Suggested for: {', '.join(c.capitalize() for c in contexts)}"

    return WellnessActionResponse(
        id=a.id,
        title=a.title,
        steps=steps,
        duration_minutes=a.duration_minutes,
        intended_contexts=contexts,
        accessibility_note=a.accessibility_note,
        source=a.source,
        review_version=a.review_version,
        is_saved=a.id in saved_ids,
        selection_reason=reason
    )

@router.get("/actions", response_model=List[WellnessActionResponse])
async def list_actions(
    context: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Fetch user's saved action ids
    saved_res = await session.execute(
        select(SavedAction.action_id).where(SavedAction.user_id == current_user.id)
    )
    saved_ids = set(saved_res.scalars().all())

    # Fetch all active actions
    actions_res = await session.execute(
        select(WellnessAction).where(WellnessAction.active == True)
    )
    actions = actions_res.scalars().all()

    formatted = [_to_action_response(a, saved_ids, context) for a in actions]

    # Prioritize actions matching selected context if requested
    if context:
        ctx_lower = context.lower()
        formatted.sort(key=lambda x: 0 if ctx_lower in x.intended_contexts else 1)

    return formatted

@router.get("/saved-actions", response_model=List[WellnessActionResponse])
async def list_saved_actions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    saved_res = await session.execute(
        select(SavedAction.action_id).where(SavedAction.user_id == current_user.id)
    )
    saved_ids = set(saved_res.scalars().all())

    actions_res = await session.execute(
        select(WellnessAction).where(WellnessAction.id.in_(saved_ids))
    )
    actions = actions_res.scalars().all()
    return [_to_action_response(a, saved_ids) for a in actions]

@router.post("/saved-actions", status_code=status.HTTP_201_CREATED)
async def save_action(
    req: SaveActionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Verify action exists
    action = await session.get(WellnessAction, req.action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found.")

    # Check if already saved
    existing = await session.execute(
        select(SavedAction).where(
            SavedAction.user_id == current_user.id,
            SavedAction.action_id == req.action_id
        )
    )
    if not existing.scalars().first():
        saved = SavedAction(
            user_id=current_user.id,
            action_id=req.action_id,
            created_at=datetime.utcnow()
        )
        session.add(saved)
        await session.commit()
    return {"message": "Action added to saved list."}

@router.delete("/saved-actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_action(
    action_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    await session.execute(
        delete(SavedAction).where(
            SavedAction.user_id == current_user.id,
            SavedAction.action_id == action_id
        )
    )
    await session.commit()
    return None

@router.post("/action-events", response_model=ActionEventResponse, status_code=status.HTTP_201_CREATED)
async def record_action_event(
    req: ActionEventCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if req.outcome not in VALID_OUTCOMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Outcome must be one of: {', '.join(sorted(VALID_OUTCOMES))}"
        )

    action = await session.get(WellnessAction, req.action_id)
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Action not found.")

    target_date = req.local_date or date.today().isoformat()
    now = datetime.utcnow()
    event = ActionEvent(
        user_id=current_user.id,
        action_id=req.action_id,
        local_date=target_date,
        outcome=req.outcome,
        user_feedback=req.user_feedback,
        created_at=now
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)

    return ActionEventResponse(
        id=event.id,
        action_id=event.action_id,
        local_date=event.local_date,
        outcome=event.outcome,
        user_feedback=event.user_feedback,
        created_at=event.created_at
    )
