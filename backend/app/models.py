import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

# ==========================================
# 1. USER AUTHENTICATION & SETTINGS
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
    timezone: str = Field(default="UTC", nullable=False)

    # Relationships
    preferences: Optional["UserPreference"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )
    consent_records: list["ConsentRecord"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    journal_entries: list["JournalEntry"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    daily_checkins: list["DailyCheckin"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    wellness_signals: list["WellnessSignal"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    baselines: list["PersonalBaseline"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    detected_changes: list["DetectedChange"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    safety_events: list["SafetyEvent"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class UserPreference(SQLModel, table=True):
    __tablename__ = "user_preferences"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, nullable=False)
    
    enable_analysis: bool = Field(default=True, nullable=False)
    trusted_contact_name: Optional[str] = Field(default=None, nullable=True)
    trusted_contact_phone: Optional[str] = Field(default=None, nullable=True)
    trusted_contact_email: Optional[str] = Field(default=None, nullable=True)

    # Relationships
    user: Optional[User] = Relationship(back_populates="preferences")


class ConsentRecord(SQLModel, table=True):
    __tablename__ = "consent_records"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    
    consent_given: bool = Field(nullable=False)
    consent_version: str = Field(default="1.0", nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="consent_records")


# ==========================================
# 2. JOURNALING & DAILY CHECK-INS
# ==========================================

class JournalEntry(SQLModel, table=True):
    __tablename__ = "journal_entries"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    
    # Text is encrypted at rest (handled at DB/service level)
    journal_text: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="journal_entries")
    wellness_signal: Optional["WellnessSignal"] = Relationship(
        back_populates="journal_entry",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )


class DailyCheckin(SQLModel, table=True):
    __tablename__ = "daily_checkins"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    
    mood: int = Field(nullable=False)  # 1: Very Difficult to 5: Very Good
    sleep: Optional[int] = Field(default=None, nullable=True) # 1-5 rating
    academic_work: bool = Field(default=False, nullable=False)
    relationships: bool = Field(default=False, nullable=False)
    social_life: bool = Field(default=False, nullable=False)
    health: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="daily_checkins")


# ==========================================
# 3. NLP WELLNESS SIGNALS & BASELINES
# ==========================================

class WellnessSignal(SQLModel, table=True):
    __tablename__ = "wellness_signals"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    journal_entry_id: uuid.UUID = Field(foreign_key="journal_entries.id", unique=True, nullable=False)
    
    # NLP-derived probabilities or scores [0.0, 1.0]
    sentiment: float = Field(default=0.0, nullable=False)
    joy: float = Field(default=0.0, nullable=False)
    sadness: float = Field(default=0.0, nullable=False)
    anger: float = Field(default=0.0, nullable=False)
    fear: float = Field(default=0.0, nullable=False)
    work_pressure: float = Field(default=0.0, nullable=False)
    sleep_issues: float = Field(default=0.0, nullable=False)
    social_support: float = Field(default=0.0, nullable=False)
    fatigue: float = Field(default=0.0, nullable=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="wellness_signals")
    journal_entry: Optional[JournalEntry] = Relationship(back_populates="wellness_signal")


class PersonalBaseline(SQLModel, table=True):
    __tablename__ = "personal_baselines"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    
    signal_name: str = Field(nullable=False)  # e.g., 'work_pressure'
    rolling_mean: float = Field(nullable=False)
    rolling_std: float = Field(nullable=False)
    window_size: int = Field(default=14, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="baselines")


# ==========================================
# 4. DEVIATION ALERTS & EXPLANATIONS
# ==========================================

class DetectedChange(SQLModel, table=True):
    __tablename__ = "detected_changes"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    
    model_type: str = Field(nullable=False)  # 'Generic' or 'Personalized'
    signal_name: str = Field(nullable=False)  # e.g., 'fatigue'
    baseline_value: float = Field(nullable=False)  # rolling baseline average or threshold
    current_value: float = Field(nullable=False)
    deviation_score: float = Field(nullable=False)  # standard deviations (z-score) or CUSUM sum
    is_flagged: bool = Field(default=False, nullable=False)
    detected_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="detected_changes")
    explanation: Optional["Explanation"] = Relationship(
        back_populates="detected_change",
        sa_relationship_kwargs={"uselist": False, "cascade": "all, delete-orphan"}
    )


class Explanation(SQLModel, table=True):
    __tablename__ = "explanations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    change_id: uuid.UUID = Field(foreign_key="detected_changes.id", unique=True, nullable=False)
    
    explanation_text: str = Field(nullable=False)
    reflection_prompt: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    detected_change: Optional[DetectedChange] = Relationship(back_populates="explanation")


# ==========================================
# 5. SAFETY EVENTS AUDIT LOG
# ==========================================

class SafetyEvent(SQLModel, table=True):
    __tablename__ = "safety_events"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    
    triggered_keyword: str = Field(nullable=False)  # Category name (redacted/general)
    action_taken: str = Field(nullable=False)  # e.g., 'Helpline modal displayed'
    triggered_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    user: Optional[User] = Relationship(back_populates="safety_events")
