import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from app.database import get_session
from app.models import User, CheckIn, ActionEvent, WellnessAction
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/reflections", tags=["Reflections & Trends"])

class MoodFrequency(BaseModel):
    mood: str
    count: int

class ContextStat(BaseModel):
    tag: str
    count: int
    associated_moods: Dict[str, int]

class ActionFeedbackSummary(BaseModel):
    action_id: str
    action_title: str
    helped_count: int
    about_same_count: int
    did_not_try_count: int

class ReflectionResponse(BaseModel):
    range_selected: str
    total_checkins: int
    date_range_start: str
    date_range_end: str
    mood_distribution: List[MoodFrequency]
    average_energy: Optional[float]
    context_summaries: List[ContextStat]
    action_feedback: List[ActionFeedbackSummary]
    non_causal_observations: List[str]
    has_sufficient_data: bool

@router.get("", response_model=ReflectionResponse)
async def get_reflections(
    range: str = Query("7d", pattern=r"^(7d|30d)$", description="Date window: 7d or 30d"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    days = 7 if range == "7d" else 30
    cutoff = datetime.utcnow() - timedelta(days=days)
    cutoff_date_str = cutoff.strftime("%Y-%m-%d")
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Fetch check-ins strictly for current user
    res = await session.execute(
        select(CheckIn)
        .where(CheckIn.user_id == current_user.id, CheckIn.local_date >= cutoff_date_str)
        .order_by(desc(CheckIn.local_date))
    )
    checkins = res.scalars().all()

    total_checkins = len(checkins)
    if total_checkins < 2:
        return ReflectionResponse(
            range_selected=range,
            total_checkins=total_checkins,
            date_range_start=cutoff_date_str,
            date_range_end=today_str,
            mood_distribution=[],
            average_energy=None,
            context_summaries=[],
            action_feedback=[],
            non_causal_observations=[
                "Reflections and trends require at least 2 recorded check-ins in this period to display non-causal patterns. Pause never invents a trend from a single entry."
            ],
            has_sufficient_data=False
        )

    # Mood frequencies
    mood_counts = Counter()
    energy_sum = 0
    energy_count = 0
    context_counts = Counter()
    context_mood_map = defaultdict(lambda: Counter())

    for c in checkins:
        if c.self_reported_mood:
            mood_counts[c.self_reported_mood] += 1
        if c.self_reported_energy is not None:
            energy_sum += c.self_reported_energy
            energy_count += 1
        
        try:
            tags = json.loads(c.context_tags)
        except Exception:
            tags = []
        for tag in tags:
            context_counts[tag] += 1
            if c.self_reported_mood:
                context_mood_map[tag][c.self_reported_mood] += 1

    mood_dist = [MoodFrequency(mood=m, count=cnt) for m, cnt in mood_counts.most_common()]
    avg_energy = round(energy_sum / energy_count, 1) if energy_count > 0 else None

    context_stats = []
    for tag, cnt in context_counts.most_common():
        context_stats.append(ContextStat(
            tag=tag,
            count=cnt,
            associated_moods=dict(context_mood_map[tag])
        ))

    # Action feedback
    action_events_res = await session.execute(
        select(ActionEvent)
        .where(ActionEvent.user_id == current_user.id, ActionEvent.local_date >= cutoff_date_str)
    )
    events = action_events_res.scalars().all()
    
    actions_res = await session.execute(select(WellnessAction))
    action_title_map = {a.id: a.title for a in actions_res.scalars().all()}

    action_counts = defaultdict(lambda: Counter())
    for ev in events:
        action_counts[ev.action_id][ev.outcome] += 1

    feedback_list = []
    for aid, counts in action_counts.items():
        feedback_list.append(ActionFeedbackSummary(
            action_id=aid,
            action_title=action_title_map.get(aid, aid),
            helped_count=counts.get("helped", 0),
            about_same_count=counts.get("about_the_same", 0),
            did_not_try_count=counts.get("did_not_try", 0)
        ))

    # Formulate careful, non-causal observations per specification
    observations = []
    for tag, cnt in context_counts.most_common(2):
        mood_breakdown = context_mood_map[tag]
        if mood_breakdown:
            breakdown_str = ", ".join(f"{m} {c} time{'s' if c > 1 else ''}" for m, c in mood_breakdown.most_common(2))
            observations.append(
                f"In {cnt} check-in{'s' if cnt > 1 else ''} tagged with '{tag.capitalize()}', you recorded {breakdown_str}. This only describes what was recorded, without implying cause."
            )

    if not observations:
        observations.append(
            f"You recorded {total_checkins} check-ins in the last {days} days. Moods and energy are displayed directly from your own entries."
        )

    return ReflectionResponse(
        range_selected=range,
        total_checkins=total_checkins,
        date_range_start=cutoff_date_str,
        date_range_end=today_str,
        mood_distribution=mood_dist,
        average_energy=avg_energy,
        context_summaries=context_stats,
        action_feedback=feedback_list,
        non_causal_observations=observations,
        has_sufficient_data=True
    )
