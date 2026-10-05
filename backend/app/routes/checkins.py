import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from app.database import get_session
from app.models import User, CheckIn
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/check-ins", tags=["Check-ins"])

ALLOWED_MOODS = {"Great", "Good", "Okay", "Uneasy", "Difficult"}
ALLOWED_CONTEXTS = {"study", "sleep", "relationships", "health", "finances", "other"}

class CheckInCreate(BaseModel):
    local_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Local date YYYY-MM-DD")
    self_reported_mood: Optional[str] = Field(None, description="Great, Good, Okay, Uneasy, Difficult")
    self_reported_energy: Optional[int] = Field(None, ge=1, le=5, description="Energy rating 1-5")
    context_tags: List[str] = Field(default_factory=list, description="Context tags influencing the day")
    note: Optional[str] = Field(None, description="Optional brief private note")

class CheckInUpdate(BaseModel):
    self_reported_mood: Optional[str] = None
    self_reported_energy: Optional[int] = Field(None, ge=1, le=5)
    context_tags: Optional[List[str]] = None
    note: Optional[str] = None

class CheckInResponse(BaseModel):
    id: uuid.UUID
    local_date: str
    self_reported_mood: Optional[str]
    self_reported_energy: Optional[int]
    context_tags: List[str]
    note: Optional[str]
    created_at: datetime
    updated_at: datetime

def _to_response(checkin: CheckIn) -> CheckInResponse:
    try:
        tags = json.loads(checkin.context_tags)
    except Exception:
        tags = []
    return CheckInResponse(
        id=checkin.id,
        local_date=checkin.local_date,
        self_reported_mood=checkin.self_reported_mood,
        self_reported_energy=checkin.self_reported_energy,
        context_tags=tags,
        note=checkin.note,
        created_at=checkin.created_at,
        updated_at=checkin.updated_at
    )

@router.get("", response_model=List[CheckInResponse])
async def list_checkins(
    limit: int = 30,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    query = (
        select(CheckIn)
        .where(CheckIn.user_id == current_user.id)
        .order_by(desc(CheckIn.local_date), desc(CheckIn.created_at))
        .offset(offset)
        .limit(min(limit, 100))
    )
    result = await session.execute(query)
    records = result.scalars().all()
    return [_to_response(r) for r in records]

@router.post("", response_model=CheckInResponse, status_code=status.HTTP_201_CREATED)
async def create_checkin(
    req: CheckInCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    if req.self_reported_mood and req.self_reported_mood not in ALLOWED_MOODS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mood must be one of: {', '.join(sorted(ALLOWED_MOODS))}"
        )

    # Clean context tags
    cleaned_tags = [t.lower() for t in req.context_tags if t.lower() in ALLOWED_CONTEXTS]
    now = datetime.utcnow()

    # Check if a checkin already exists for this date, if so update or allow multiple?
    # Spec: Let user save, edit, skip, delete. If exists for date, we can allow or update.
    # Let's create new checkin record
    checkin = CheckIn(
        user_id=current_user.id,
        local_date=req.local_date,
        self_reported_mood=req.self_reported_mood,
        self_reported_energy=req.self_reported_energy,
        context_tags=json.dumps(cleaned_tags),
        note=req.note,
        created_at=now,
        updated_at=now
    )
    session.add(checkin)
    await session.commit()
    await session.refresh(checkin)
    return _to_response(checkin)

@router.patch("/{checkin_id}", response_model=CheckInResponse)
async def update_checkin(
    checkin_id: uuid.UUID,
    req: CheckInUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(CheckIn).where(CheckIn.id == checkin_id, CheckIn.user_id == current_user.id)
    )
    checkin = result.scalars().first()
    if not checkin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found.")

    if req.self_reported_mood is not None:
        if req.self_reported_mood and req.self_reported_mood not in ALLOWED_MOODS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid mood choice.")
        checkin.self_reported_mood = req.self_reported_mood

    if req.self_reported_energy is not None:
        checkin.self_reported_energy = req.self_reported_energy

    if req.context_tags is not None:
        cleaned_tags = [t.lower() for t in req.context_tags if t.lower() in ALLOWED_CONTEXTS]
        checkin.context_tags = json.dumps(cleaned_tags)

    if req.note is not None:
        checkin.note = req.note

    checkin.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(checkin)
    return _to_response(checkin)

@router.delete("/{checkin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_checkin(
    checkin_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(CheckIn).where(CheckIn.id == checkin_id, CheckIn.user_id == current_user.id)
    )
    checkin = result.scalars().first()
    if not checkin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Check-in not found.")

    await session.delete(checkin)
    await session.commit()
    return None
