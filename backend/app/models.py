import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship

# ==========================================
# 1. USER & CONSENT MANAGEMENT
# ==========================================

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )
    email: str = Field(unique=True, index=True, nullable=False)
    password_hash: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    locale: str = Field(default="en-IN", nullable=False)
    selected_country: str = Field(default="IN", nullable=False)
    confirmed_18_plus: bool = Field(default=False, nullable=False)
    is_demo_account: bool = Field(default=False, nullable=False)

    # Relationships
    consents: List["ConsentRecord"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    check_ins: List["CheckIn"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    journal_entries: List["JournalEntry"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    daily_plans: List["DailyPlan"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    saved_actions: List["SavedAction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    action_events: List["ActionEvent"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ConsentRecord(SQLModel, table=True):
    __tablename__ = "consent_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    # Purposes: 'save_journal', 'emotion_analysis', 'embeddings_rag', 'external_inference'
    purpose: str = Field(nullable=False, index=True)
    policy_version: str = Field(default="1.0", nullable=False)
    granted: bool = Field(default=False, nullable=False)
    granted_at: Optional[datetime] = Field(default=None, nullable=True)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)

    user: Optional[User] = Relationship(back_populates="consents")


# ==========================================
# 2. CHECK-INS & JOURNAL ENTRIES
# ==========================================

class CheckIn(SQLModel, table=True):
    __tablename__ = "check_ins"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    local_date: str = Field(index=True, nullable=False) # Format: YYYY-MM-DD
    # Mood: 5 plain-language choices: Great, Good, Okay, Uneasy, Difficult
    self_reported_mood: Optional[str] = Field(default=None, nullable=True)
    # Energy: 1 to 5 scale
    self_reported_energy: Optional[int] = Field(default=None, nullable=True)
    # Context tags: JSON array ["study", "sleep", "relationships", "health", "finances", "other"]
    context_tags: str = Field(default="[]", nullable=False)
    note: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[User] = Relationship(back_populates="check_ins")


class JournalEntry(SQLModel, table=True):
    __tablename__ = "journal_entries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # Ciphertext encrypted at application level using Fernet key
    encrypted_text: str = Field(nullable=False)
    language: str = Field(default="en", nullable=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True, index=True)

    user: Optional[User] = Relationship(back_populates="journal_entries")
    emotion_analysis: Optional["EmotionAnalysis"] = Relationship(
        back_populates="entry",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    embedding: Optional["EntryEmbedding"] = Relationship(
        back_populates="entry",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )


# ==========================================
# 3. AI ANALYSIS & EMBEDDINGS (SEPARATED)
# ==========================================

class EmotionAnalysis(SQLModel, table=True):
    __tablename__ = "emotion_analyses"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    entry_id: uuid.UUID = Field(foreign_key="journal_entries.id", unique=True, index=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    model_id: str = Field(nullable=False)
    model_version: str = Field(nullable=False)
    # JSON array of tentative non-clinical labels
    labels: str = Field(default="[]", nullable=False)
    # JSON array of confidence qualifiers ("tentative", "uncertain"), no false precision
    confidence_bands: str = Field(default="[]", nullable=False)
    # JSON array of matched phrase snippets
    explanation_spans: str = Field(default="[]", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # User can correct or override labels
    user_correction: Optional[str] = Field(default=None, nullable=True)
    hidden: bool = Field(default=False, nullable=False)

    entry: Optional[JournalEntry] = Relationship(back_populates="emotion_analysis")


class EntryEmbedding(SQLModel, table=True):
    __tablename__ = "entry_embeddings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    entry_id: uuid.UUID = Field(foreign_key="journal_entries.id", unique=True, index=True, nullable=False)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    # Stored as JSON array of floats for portable SQL filtering + exact cosine similarity
    embedding_json: str = Field(nullable=False)
    model_id: str = Field(nullable=False)
    model_version: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    entry: Optional[JournalEntry] = Relationship(back_populates="embedding")


# ==========================================
# 4. ONE-THING PLAN & WELLNESS ACTIONS
# ==========================================

class DailyPlan(SQLModel, table=True):
    __tablename__ = "daily_plans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    local_date: str = Field(index=True, nullable=False) # YYYY-MM-DD
    focus: str = Field(nullable=False)
    # Up to 3 small editable steps: [{"id": "1", "text": "...", "completed": false}]
    steps_json: str = Field(default="[]", nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[User] = Relationship(back_populates="daily_plans")


class WellnessAction(SQLModel, table=True):
    __tablename__ = "wellness_actions"

    id: str = Field(primary_key=True) # e.g. "box-breathing", "break-it-down"
    title: str = Field(nullable=False)
    steps_json: str = Field(nullable=False) # JSON array of step instructions
    duration_minutes: int = Field(default=5, nullable=False)
    intended_contexts_json: str = Field(default="[]", nullable=False) # JSON array: ["study", "sleep", ...]
    accessibility_note: str = Field(default="", nullable=False)
    source: str = Field(default="Clinical & Student Wellness Reviewed Catalog", nullable=False)
    review_version: str = Field(default="2026.1", nullable=False)
    active: bool = Field(default=True, nullable=False)


class SavedAction(SQLModel, table=True):
    __tablename__ = "saved_actions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    action_id: str = Field(foreign_key="wellness_actions.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[User] = Relationship(back_populates="saved_actions")


class ActionEvent(SQLModel, table=True):
    __tablename__ = "action_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    action_id: str = Field(foreign_key="wellness_actions.id", nullable=False)
    local_date: str = Field(nullable=False)
    # Outcome: 'helped', 'about_the_same', 'did_not_try', 'skipped'
    outcome: str = Field(nullable=False)
    user_feedback: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    user: Optional[User] = Relationship(back_populates="action_events")


# ==========================================
# 5. SUPPORT RESOURCES & AUDIT LOGS
# ==========================================

class SupportResource(SQLModel, table=True):
    __tablename__ = "support_resources"

    id: str = Field(primary_key=True)
    region: str = Field(default="IN", index=True, nullable=False)
    display_name: str = Field(nullable=False)
    contact: str = Field(nullable=False)
    type: str = Field(default="helpline", nullable=False) # helpline, emergency, campus
    source_url: str = Field(nullable=False)
    verified_at: str = Field(nullable=False)
    language_notes: str = Field(default="Multilingual", nullable=False)


class AuditEvent(SQLModel, table=True):
    """
    Security and administrative audit events only.
    STRICT PRIVACY REQUIREMENT: Never store journal text, prompts, embeddings,
    emotion labels, or crisis text in this table or logs.
    """
    __tablename__ = "audit_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: Optional[uuid.UUID] = Field(default=None, index=True, nullable=True)
    action: str = Field(nullable=False) # e.g. "AUTH_LOGIN", "DATA_EXPORT", "ACCOUNT_DELETE"
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    status: str = Field(default="SUCCESS", nullable=False)
    client_ip: Optional[str] = Field(default=None, nullable=True)
