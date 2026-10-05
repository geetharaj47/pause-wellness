import json
import uuid
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import User, DailyPlan
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/daily-plan", tags=["One-Thing Daily Plan"])

class PlanStep(BaseModel):
    id: str
    text: str
    completed: bool = False

class PlanUpdate(BaseModel):
    local_date: Optional[str] = None
    focus: str = Field(..., min_length=1, description="One primary priority or gentle focus for the day")
    steps: List[PlanStep] = Field(default_factory=list, max_length=3, description="Up to 3 small, manageable steps")

class PlanResponse(BaseModel):
    id: uuid.UUID
    local_date: str
    focus: str
    steps: List[PlanStep]
    updated_at: datetime

def _format_plan(p: DailyPlan) -> PlanResponse:
    try:
        steps_raw = json.loads(p.steps_json)
        steps = [PlanStep(**s) for s in steps_raw]
    except Exception:
        steps = []
    return PlanResponse(
        id=p.id,
        local_date=p.local_date,
        focus=p.focus,
        steps=steps,
        updated_at=p.updated_at
    )

@router.get("/today", response_model=Optional[PlanResponse])
async def get_today_plan(
    local_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    target_date = local_date or date.today().isoformat()
    result = await session.execute(
        select(DailyPlan).where(
            DailyPlan.user_id == current_user.id,
            DailyPlan.local_date == target_date
        )
    )
    plan = result.scalars().first()
    if not plan:
        return None
    return _format_plan(plan)

@router.put("/today", response_model=PlanResponse)
async def upsert_today_plan(
    req: PlanUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    target_date = req.local_date or date.today().isoformat()
    now = datetime.utcnow()

    # Steps limited to 3 per specification
    steps_data = [s.model_dump() for s in req.steps[:3]]
    steps_json = json.dumps(steps_data)

    result = await session.execute(
        select(DailyPlan).where(
            DailyPlan.user_id == current_user.id,
            DailyPlan.local_date == target_date
        )
    )
    plan = result.scalars().first()
    if not plan:
        plan = DailyPlan(
            user_id=current_user.id,
            local_date=target_date,
            focus=req.focus,
            steps_json=steps_json,
            updated_at=now
        )
        session.add(plan)
    else:
        plan.focus = req.focus
        plan.steps_json = steps_json
        plan.updated_at = now

    await session.commit()
    await session.refresh(plan)
    return _format_plan(plan)

@router.delete("/today", status_code=status.HTTP_204_NO_CONTENT)
async def delete_today_plan(
    local_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    target_date = local_date or date.today().isoformat()
    result = await session.execute(
        select(DailyPlan).where(
            DailyPlan.user_id == current_user.id,
            DailyPlan.local_date == target_date
        )
    )
    plan = result.scalars().first()
    if plan:
        await session.delete(plan)
        await session.commit()
    return None
