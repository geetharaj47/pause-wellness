import json
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc, delete

from sqlalchemy.orm import selectinload
from app.database import get_session
from app.models import User, JournalEntry, EmotionAnalysis, EntryEmbedding, ConsentRecord
from app.auth import get_current_user
from app.security import encrypt_journal_text, decrypt_journal_text

router = APIRouter(prefix="/api/v1/journal", tags=["Journal Entries"])

class JournalCreate(BaseModel):
    text: str = Field(..., min_length=1, description="Raw private journal text")
    language: str = Field(default="en", description="ISO language code, default en")

class JournalUpdate(BaseModel):
    text: str = Field(..., min_length=1, description="Updated journal text")

class EmotionAnalysisSummary(BaseModel):
    id: uuid.UUID
    model_id: str
    model_version: str
    labels: List[str]
    confidence_bands: List[str]
    explanation_spans: List[str]
    user_correction: Optional[str]
    hidden: bool
    created_at: datetime

class JournalResponse(BaseModel):
    id: uuid.UUID
    text: str
    language: str
    created_at: datetime
    updated_at: datetime
    emotion_analysis: Optional[EmotionAnalysisSummary] = None

def _format_entry(entry: JournalEntry, analysis_override: Optional[EmotionAnalysis] = None) -> JournalResponse:
    decrypted = decrypt_journal_text(entry.encrypted_text)
    analysis_summary = None
    ea = analysis_override
    if ea is None and "emotion_analysis" in entry.__dict__:
        ea = entry.emotion_analysis

    if ea and not ea.hidden:
        try:
            labels = json.loads(ea.labels)
        except Exception:
            labels = []
        try:
            bands = json.loads(ea.confidence_bands)
        except Exception:
            bands = []
        try:
            spans = json.loads(ea.explanation_spans)
        except Exception:
            spans = []

        analysis_summary = EmotionAnalysisSummary(
            id=ea.id,
            model_id=ea.model_id,
            model_version=ea.model_version,
            labels=labels,
            confidence_bands=bands,
            explanation_spans=spans,
            user_correction=ea.user_correction,
            hidden=ea.hidden,
            created_at=ea.created_at
        )

    return JournalResponse(
        id=entry.id,
        text=decrypted,
        language=entry.language,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        emotion_analysis=analysis_summary
    )

@router.get("", response_model=List[JournalResponse])
async def list_journal_entries(
    limit: int = 30,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    query = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.emotion_analysis))
        .where(JournalEntry.user_id == current_user.id, JournalEntry.deleted_at == None)
        .order_by(desc(JournalEntry.created_at))
        .offset(offset)
        .limit(min(limit, 100))
    )
    result = await session.execute(query)
    entries = result.scalars().all()
    return [_format_entry(e) for e in entries]

@router.post("", response_model=JournalResponse, status_code=status.HTTP_201_CREATED)
async def create_journal_entry(
    req: JournalCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Verify save_journal consent
    consent_res = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose == "save_journal"
        )
    )
    consent = consent_res.scalars().first()
    if not consent or not consent.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Journal saving is currently disabled in your consent settings. Enable 'Save journal entries' in Privacy settings to save."
        )

    now = datetime.utcnow()
    cipher = encrypt_journal_text(req.text)
    entry = JournalEntry(
        user_id=current_user.id,
        created_at=now,
        updated_at=now,
        encrypted_text=cipher,
        language=req.language or "en",
        deleted_at=None
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return _format_entry(entry, analysis_override=None)

@router.get("/{entry_id}", response_model=JournalResponse)
async def get_journal_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(JournalEntry)
        .options(selectinload(JournalEntry.emotion_analysis))
        .where(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id,
            JournalEntry.deleted_at == None
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")
    return _format_entry(entry)

@router.patch("/{entry_id}", response_model=JournalResponse)
async def update_journal_entry(
    entry_id: uuid.UUID,
    req: JournalUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id,
            JournalEntry.deleted_at == None
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")

    entry.encrypted_text = encrypt_journal_text(req.text)
    entry.updated_at = datetime.utcnow()

    # Invalidate existing embedding when text changes
    await session.execute(
        delete(EntryEmbedding).where(EntryEmbedding.entry_id == entry.id)
    )

    await session.commit()
    await session.refresh(entry)
    return _format_entry(entry, analysis_override=None)

@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journal_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(JournalEntry).where(
            JournalEntry.id == entry_id,
            JournalEntry.user_id == current_user.id
        )
    )
    entry = result.scalars().first()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found.")

    # Transactional cascading deletion of entry, analyses, and embeddings
    await session.execute(delete(EmotionAnalysis).where(EmotionAnalysis.entry_id == entry_id))
    await session.execute(delete(EntryEmbedding).where(EntryEmbedding.entry_id == entry_id))
    await session.delete(entry)
    await session.commit()
    return None
