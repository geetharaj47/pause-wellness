import json
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel, select
from app.config import settings
from app.models import WellnessAction, SupportResource

connect_args = {}
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

# Use NullPool with asyncpg to guarantee no cross-event-loop connection sharing
engine = create_async_engine(
    db_url,
    echo=False,
    poolclass=NullPool,
    connect_args=connect_args
)

async_session_maker = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency provider yielding async sessions for FastAPI handlers."""
    async with async_session_maker() as session:
        yield session

async def seed_initial_data(session: AsyncSession) -> None:
    """Seed reviewed wellness actions and verified support resources if empty."""
    # Check actions
    action_check = await session.execute(select(WellnessAction).limit(1))
    if not action_check.scalars().first():
        actions = [
            WellnessAction(
                id="box-breathing",
                title="Box Breathing (4-4-4-4)",
                steps_json=json.dumps([
                    "Inhale smoothly through your nose for 4 counts.",
                    "Gently hold your breath for 4 counts.",
                    "Exhale slowly through your mouth for 4 counts.",
                    "Rest and hold for 4 counts before the next cycle.",
                    "Repeat 3 to 4 times or stop whenever you choose."
                ]),
                duration_minutes=3,
                intended_contexts_json=json.dumps(["stress", "worry", "sleep", "study"]),
                accessibility_note="Can be performed sitting or lying down without making any sound.",
                source="Reviewed Clinical & Student Wellness Catalog",
                review_version="2026.1",
                active=True
            ),
            WellnessAction(
                id="break-it-down",
                title="Micro-Step Task Slicing",
                steps_json=json.dumps([
                    "Write down the single task that feels heavy right now.",
                    "Shrink it to an absurdly small first step (e.g. open the slide or write 1 sentence).",
                    "Commit to only doing that one step for 2 minutes.",
                    "Give yourself permission to pause right after."
                ]),
                duration_minutes=4,
                intended_contexts_json=json.dumps(["study", "stress", "finances"]),
                accessibility_note="Can be typed, written on paper, or thought through quietly.",
                source="Student Cognitive Reframing Protocols",
                review_version="2026.1",
                active=True
            ),
            WellnessAction(
                id="sensory-grounding",
                title="5-4-3-2-1 Sensory Reset",
                steps_json=json.dumps([
                    "Notice 5 things you can see around your current space.",
                    "Notice 4 physical textures or contact points you can feel.",
                    "Notice 3 distinct sounds in your environment.",
                    "Notice 2 things you can smell or subtle scents.",
                    "Notice 1 positive or neutral sensation in your body right now."
                ]),
                duration_minutes=3,
                intended_contexts_json=json.dumps(["stress", "worry", "other"]),
                accessibility_note="Easily adaptable for varying visual, auditory, or mobility preferences.",
                source="Mindfulness & Somatic Grounding Review",
                review_version="2026.1",
                active=True
            ),
            WellnessAction(
                id="transition-rest",
                title="Study-to-Rest Transition Ritual",
                steps_json=json.dumps([
                    "Close study tabs, save current work, and write a 1-line note where you will start tomorrow.",
                    "Physically step away from your desk or workspace.",
                    "Drink a glass of water and roll your shoulders back.",
                    "Mentally acknowledge: 'Today's study window is complete.'"
                ]),
                duration_minutes=5,
                intended_contexts_json=json.dumps(["study", "sleep", "health"]),
                accessibility_note="No physical exertion required.",
                source="University Academic Wellness Guidelines",
                review_version="2026.1",
                active=True
            ),
            WellnessAction(
                id="reconnect-ping",
                title="Low-Pressure Reconnect Message",
                steps_json=json.dumps([
                    "Think of a friend or family member you feel safe with.",
                    "Draft a low-pressure message without needing an immediate answer (e.g. 'Thinking of you, hope your week is going gently!').",
                    "Send it and put your phone face down."
                ]),
                duration_minutes=2,
                intended_contexts_json=json.dumps(["relationships", "lonely", "other"]),
                accessibility_note="Can be sent via any preferred messaging channel or written privately.",
                source="Social Connectedness Interventions Review",
                review_version="2026.1",
                active=True
            ),
            WellnessAction(
                id="calm-bedtime",
                title="Calmer Bedtime Wind-Down",
                steps_json=json.dumps([
                    "Lower room lighting and switch your phone to silent/do-not-disturb.",
                    "Take 5 unhurried slow breaths with your eyes closed.",
                    "Release tension in your jaw, forehead, and shoulders.",
                    "Let go of planning tomorrow until you wake."
                ]),
                duration_minutes=8,
                intended_contexts_json=json.dumps(["sleep", "health", "stress"]),
                accessibility_note="Suitable for any bedroom setup.",
                source="Sleep Hygiene & Behavioral Review",
                review_version="2026.1",
                active=True
            )
        ]
        for a in actions:
            session.add(a)

    # Check support resources
    support_check = await session.execute(select(SupportResource).limit(1))
    if not support_check.scalars().first():
        resources = [
            SupportResource(
                id="tele-manas-14416",
                region="IN",
                display_name="Tele-MANAS (Govt of India)",
                contact="14416 / 1800-89-14416",
                type="helpline",
                source_url="https://dghs.mohfw.gov.in/national-mental-health-programme.php",
                verified_at="2026-09-01",
                language_notes="Toll-free, 24/7, 20+ Indian languages. Free tele-mental health support."
            ),
            SupportResource(
                id="national-emergency-112",
                region="IN",
                display_name="National Emergency Number",
                contact="112",
                type="emergency",
                source_url="https://112.gov.in/",
                verified_at="2026-09-01",
                language_notes="All-India emergency response service (police, fire, medical)."
            ),
            SupportResource(
                id="kiran-helpline",
                region="IN",
                display_name="KIRAN Mental Health Rehabilitation Helpline",
                contact="1800-599-0019",
                type="helpline",
                source_url="https://depwd.gov.in/",
                verified_at="2026-09-01",
                language_notes="Ministry of Social Justice, 24/7 support in 13 languages."
            ),
            SupportResource(
                id="vandrevala-foundation",
                region="IN",
                display_name="Vandrevala Foundation Helpline",
                contact="+91 9999 666 555",
                type="helpline",
                source_url="https://www.vandrevalafoundation.com",
                verified_at="2026-09-01",
                language_notes="Free, confidential 24/7 mental wellness counseling."
            )
        ]
        for r in resources:
            session.add(r)

    await session.commit()

async def init_db() -> None:
    """Initializes tables and seeds base records."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with async_session_maker() as session:
        await seed_initial_data(session)
