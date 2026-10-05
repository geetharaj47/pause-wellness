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
from app.models import User, JournalEntry, EmotionAnalysis, EntryEmbedding, ConsentRecord, RagFeedback
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
    await session.flush()

    # Generate embedding if embeddings_rag consent is enabled
    rag_consent_res = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose == "embeddings_rag"
        )
    )
    rag_consent = rag_consent_res.scalars().first()
    if rag_consent and rag_consent.granted:
        from app.services.embedding_service import embedding_service
        vector = embedding_service.embed_text(req.text)
        session.add(EntryEmbedding(
            entry_id=entry.id,
            user_id=current_user.id,
            embedding_json=json.dumps(vector),
            model_id=embedding_service.model_id,
            model_version=embedding_service.model_version,
            created_at=now
        ))

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

# ==========================================
# EMOTION ANALYSIS ENDPOINTS
# ==========================================

from app.services.emotion_service import emotion_service
from app.services.crisis_service import crisis_service

class EmotionCorrectionRequest(BaseModel):
    user_correction: Optional[str] = None
    corrected_labels: Optional[List[str]] = None
    hidden: Optional[bool] = None

class EmotionAnalysisResponse(BaseModel):
    id: uuid.UUID
    entry_id: uuid.UUID
    status: str
    model_id: str
    model_version: str
    labels: List[str]
    confidence_bands: List[str]
    explanation_spans: List[str]
    user_facing_explanation: str
    user_correction: Optional[str] = None
    hidden: bool = False
    abstained: bool = False
    created_at: datetime

@router.post("/{entry_id}/analyze", response_model=EmotionAnalysisResponse)
async def analyze_journal_entry(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Explicitly analyze a submitted journal entry.
    Gated by user consent and language checks.
    """
    # 1. Verify emotion_analysis consent
    consent_res = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose == "emotion_analysis"
        )
    )
    consent = consent_res.scalars().first()
    if not consent or not consent.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Emotion analysis requires explicit consent. Please enable 'Emotion analysis suggestions' under Privacy settings."
        )

    # 2. Fetch journal entry scoped to owner
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

    decrypted_text = decrypt_journal_text(entry.encrypted_text)

    # 3. Dedicated safety check: run crisis detector before emotion model
    crisis_res = crisis_service.evaluate_text(decrypted_text)
    if crisis_res.detected_class == "explicit_urgent_language":
        # Pause generation and return crisis support response
        return EmotionAnalysisResponse(
            id=uuid.uuid4(),
            entry_id=entry.id,
            status="crisis_support",
            model_id=crisis_res.model_id,
            model_version=crisis_res.model_version,
            labels=[],
            confidence_bands=[],
            explanation_spans=[],
            user_facing_explanation=crisis_res.user_message,
            user_correction=None,
            hidden=False,
            abstained=True,
            created_at=datetime.utcnow()
        )

    # 4. Execute analysis through EmotionAnalysisService
    analysis_res = emotion_service.analyze(decrypted_text, language=entry.language)

    now = datetime.utcnow()
    labels_json = json.dumps(analysis_res["labels"])
    bands_json = json.dumps(analysis_res["confidence_bands"])
    spans_json = json.dumps(analysis_res["explanation_spans"])

    # 4. Check if analysis record already exists (idempotent / versioned)
    existing_res = await session.execute(
        select(EmotionAnalysis).where(EmotionAnalysis.entry_id == entry_id)
    )
    analysis_record = existing_res.scalars().first()

    if not analysis_record:
        analysis_record = EmotionAnalysis(
            entry_id=entry.id,
            user_id=current_user.id,
            model_id=analysis_res["model_id"],
            model_version=analysis_res["model_version"],
            labels=labels_json,
            confidence_bands=bands_json,
            explanation_spans=spans_json,
            created_at=now,
            user_correction=None,
            hidden=False
        )
        session.add(analysis_record)
    else:
        analysis_record.model_id = analysis_res["model_id"]
        analysis_record.model_version = analysis_res["model_version"]
        analysis_record.labels = labels_json
        analysis_record.confidence_bands = bands_json
        analysis_record.explanation_spans = spans_json
        analysis_record.created_at = now
        analysis_record.hidden = False

    await session.commit()
    await session.refresh(analysis_record)

    return EmotionAnalysisResponse(
        id=analysis_record.id,
        entry_id=analysis_record.entry_id,
        status=analysis_res["status"],
        model_id=analysis_record.model_id,
        model_version=analysis_record.model_version,
        labels=analysis_res["labels"],
        confidence_bands=analysis_res["confidence_bands"],
        explanation_spans=analysis_res["explanation_spans"],
        user_facing_explanation=analysis_res["user_facing_explanation"],
        user_correction=analysis_record.user_correction,
        hidden=analysis_record.hidden,
        abstained=analysis_res["abstained"],
        created_at=analysis_record.created_at
    )

@router.patch("/{entry_id}/analysis", response_model=EmotionAnalysisResponse)
async def update_emotion_analysis(
    entry_id: uuid.UUID,
    req: EmotionCorrectionRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Allow user to correct, hide, or override tentative emotion tags.
    Never modifies user's own check-in values.
    """
    result = await session.execute(
        select(EmotionAnalysis).where(
            EmotionAnalysis.entry_id == entry_id,
            EmotionAnalysis.user_id == current_user.id
        )
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No analysis found for this entry.")

    if req.corrected_labels is not None:
        analysis.labels = json.dumps([str(l) for l in req.corrected_labels[:3]])
    if req.user_correction is not None:
        analysis.user_correction = req.user_correction
    if req.hidden is not None:
        analysis.hidden = req.hidden

    await session.commit()
    await session.refresh(analysis)

    try:
        labels = json.loads(analysis.labels)
    except Exception:
        labels = []
    try:
        bands = json.loads(analysis.confidence_bands)
    except Exception:
        bands = []
    try:
        spans = json.loads(analysis.explanation_spans)
    except Exception:
        spans = []

    return EmotionAnalysisResponse(
        id=analysis.id,
        entry_id=analysis.entry_id,
        status="corrected" if analysis.user_correction else "success",
        model_id=analysis.model_id,
        model_version=analysis.model_version,
        labels=labels,
        confidence_bands=bands,
        explanation_spans=spans,
        user_facing_explanation="Analysis updated with your correction.",
        user_correction=analysis.user_correction,
        hidden=analysis.hidden,
        abstained=len(labels) == 0,
        created_at=analysis.created_at
    )

@router.delete("/{entry_id}/analysis", status_code=status.HTTP_204_NO_CONTENT)
async def delete_emotion_analysis(
    entry_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Independently delete emotion analysis while preserving the original journal entry.
    """
    result = await session.execute(
        select(EmotionAnalysis).where(
            EmotionAnalysis.entry_id == entry_id,
            EmotionAnalysis.user_id == current_user.id
        )
    )
    analysis = result.scalars().first()
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found.")

    await session.delete(analysis)
    await session.commit()
    return None

# ==========================================
# HYBRID SEMANTIC SEARCH (ASK MY HISTORY)
# ==========================================

from app.services.embedding_service import embedding_service, RELEVANCE_THRESHOLD

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question or search query about previous reflections")
    top_k: int = Field(default=5, ge=1, le=20)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class SearchResultItem(BaseModel):
    entry_id: uuid.UUID
    created_at: datetime
    date_formatted: str
    snippet: str
    similarity_score: float
    lexical_score: float
    combined_score: float

class SearchResponse(BaseModel):
    query: str
    total_retrieved: int
    relevance_threshold: float
    abstained: bool
    message: str
    results: List[SearchResultItem]

@router.post("/search", response_model=SearchResponse)
async def search_journal_entries(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Search only entries belonging to the authenticated user.
    Gated by embeddings_rag consent.
    Tenant filter is strictly applied in the database query BEFORE ranking/top-k.
    """
    # 1. Verify embeddings_rag consent
    consent_res = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose == "embeddings_rag"
        )
    )
    consent = consent_res.scalars().first()
    if not consent or not consent.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Personal history search requires 'Personal history semantic search' consent. Please enable it in Privacy settings."
        )

    # 2. Query only authenticated user's embeddings in the database query before vector ranking
    stmt = (
        select(EntryEmbedding, JournalEntry)
        .join(JournalEntry, EntryEmbedding.entry_id == JournalEntry.id)
        .where(
            EntryEmbedding.user_id == current_user.id,
            JournalEntry.user_id == current_user.id,
            JournalEntry.deleted_at == None
        )
    )
    if req.start_date:
        stmt = stmt.where(JournalEntry.created_at >= req.start_date)
    if req.end_date:
        stmt = stmt.where(JournalEntry.created_at <= req.end_date)

    rows = (await session.execute(stmt)).all()
    if not rows:
        return SearchResponse(
            query=req.query,
            total_retrieved=0,
            relevance_threshold=RELEVANCE_THRESHOLD,
            abstained=True,
            message="I couldn't find a related entry in your previous reflections.",
            results=[]
        )

    # 3. Compute query embedding
    q_vec = embedding_service.embed_text(req.query)

    # 4. Rank items with hybrid scoring
    scored_items = []
    for emb, entry in rows:
        try:
            stored_vector = json.loads(emb.embedding_json)
        except Exception:
            continue

        decrypted_text = decrypt_journal_text(entry.encrypted_text)
        cosine_sim = embedding_service.cosine_similarity(q_vec, stored_vector)
        lexical_score = embedding_service.lexical_keyword_score(req.query, decrypted_text)
        combined_score = (0.75 * cosine_sim) + (0.25 * lexical_score)

        # Relevance gate
        if combined_score >= RELEVANCE_THRESHOLD:
            snippet = decrypted_text[:220] + ("..." if len(decrypted_text) > 220 else "")
            date_fmt = entry.created_at.strftime("%b %d, %Y")
            scored_items.append(SearchResultItem(
                entry_id=entry.id,
                created_at=entry.created_at,
                date_formatted=date_fmt,
                snippet=snippet,
                similarity_score=round(cosine_sim, 4),
                lexical_score=round(lexical_score, 4),
                combined_score=round(combined_score, 4)
            ))

    scored_items.sort(key=lambda x: x.combined_score, reverse=True)
    top_results = scored_items[:req.top_k]

    if not top_results:
        return SearchResponse(
            query=req.query,
            total_retrieved=0,
            relevance_threshold=RELEVANCE_THRESHOLD,
            abstained=True,
            message="I couldn't find a related entry in your previous reflections.",
            results=[]
        )

    return SearchResponse(
        query=req.query,
        total_retrieved=len(top_results),
        relevance_threshold=RELEVANCE_THRESHOLD,
        abstained=False,
        message=f"Found {len(top_results)} relevant reflection{'s' if len(top_results) > 1 else ''}.",
        results=top_results
    )

@router.post("/sync-embeddings")
async def sync_embeddings(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Ensure all existing non-deleted journal entries for the current user
    have vector embeddings if embeddings_rag consent is enabled.
    """
    consent_res = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose == "embeddings_rag"
        )
    )
    consent = consent_res.scalars().first()
    if not consent or not consent.granted:
        return {"status": "skipped", "message": "Embeddings consent is not active."}

    existing_embs_res = await session.execute(
        select(EntryEmbedding.entry_id).where(EntryEmbedding.user_id == current_user.id)
    )
    embedded_ids = set(existing_embs_res.scalars().all())

    all_entries_res = await session.execute(
        select(JournalEntry).where(
            JournalEntry.user_id == current_user.id,
            JournalEntry.deleted_at == None
        )
    )
    entries = all_entries_res.scalars().all()

    now = datetime.utcnow()
    added_count = 0
    for e in entries:
        if e.id not in embedded_ids:
            text = decrypt_journal_text(e.encrypted_text)
            vector = embedding_service.embed_text(text)
            session.add(EntryEmbedding(
                entry_id=e.id,
                user_id=current_user.id,
                embedding_json=json.dumps(vector),
                model_id=embedding_service.model_id,
                model_version=embedding_service.model_version,
                created_at=now
            ))
            added_count += 1

    await session.commit()
    return {"status": "success", "synced_count": added_count}


# ==========================================
# RAG ANSWER GENERATION & CITATION VALIDATION
# ==========================================

from app.services.rag_service import rag_service

class RAGAskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Question about past reflections")
    top_k: int = Field(default=5, ge=1, le=20)
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class RAGAskResponse(BaseModel):
    query: str
    answer: Optional[str] = None
    source_entry_ids: List[uuid.UUID]
    sources: List[SearchResultItem]
    abstained: bool
    safety_route: str
    message: str
    provider: str

class RAGFeedbackRequest(BaseModel):
    query: str = Field(..., min_length=1)
    feedback_type: str = Field(default="not_accurate")

@router.post("/ask", response_model=RAGAskResponse)
async def ask_my_history(
    req: RAGAskRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    RAG personal-history generation with strict citation validation and safety guardrails:
    1. Gated by embeddings_rag consent.
    2. Untrusted data boundary: safety pre-check for crisis, prompt injection, and clinical claims.
    3. Tenant isolation in SQL query before ranking.
    4. Relevance threshold gate (0.38) with honest abstention.
    5. Grounded synthesis citing only validated retrieved entry IDs.
    """
    # 1. Verify consent
    consent_res = await session.execute(
        select(ConsentRecord).where(
            ConsentRecord.user_id == current_user.id,
            ConsentRecord.purpose == "embeddings_rag"
        )
    )
    consent = consent_res.scalars().first()
    if not consent or not consent.granted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Personal history search requires 'Personal history semantic search' consent. Please enable it in Privacy settings."
        )

    # 2. Safety pre-check (crisis, prompt injection, clinical claims)
    safety_route, refusal_msg = rag_service.check_safety_and_adversarial(req.query)
    if safety_route:
        return RAGAskResponse(
            query=req.query,
            answer=None,
            source_entry_ids=[],
            sources=[],
            abstained=True,
            safety_route=safety_route,
            message=refusal_msg or "Query flagged by safety check.",
            provider="safety_guardrail"
        )

    # 3. Tenant-isolated query in database before ranking
    stmt = (
        select(EntryEmbedding, JournalEntry)
        .join(JournalEntry, EntryEmbedding.entry_id == JournalEntry.id)
        .where(
            EntryEmbedding.user_id == current_user.id,
            JournalEntry.user_id == current_user.id,
            JournalEntry.deleted_at == None
        )
    )
    if req.start_date:
        stmt = stmt.where(JournalEntry.created_at >= req.start_date)
    if req.end_date:
        stmt = stmt.where(JournalEntry.created_at <= req.end_date)

    rows = (await session.execute(stmt)).all()
    if not rows:
        return RAGAskResponse(
            query=req.query,
            answer=None,
            source_entry_ids=[],
            sources=[],
            abstained=True,
            safety_route="normal",
            message="I couldn't find a related entry in your previous reflections.",
            provider=rag_service.generator_mode
        )

    # 4. Hybrid ranking
    q_vec = embedding_service.embed_text(req.query)
    scored_items = []
    for emb, entry in rows:
        try:
            stored_vector = json.loads(emb.embedding_json)
        except Exception:
            continue

        decrypted_text = decrypt_journal_text(entry.encrypted_text)
        cosine_sim = embedding_service.cosine_similarity(q_vec, stored_vector)
        lexical_score = embedding_service.lexical_keyword_score(req.query, decrypted_text)
        combined_score = (0.75 * cosine_sim) + (0.25 * lexical_score)

        if combined_score >= RELEVANCE_THRESHOLD:
            snippet = decrypted_text[:280] + ("..." if len(decrypted_text) > 280 else "")
            date_fmt = entry.created_at.strftime("%b %d, %Y")
            scored_items.append({
                "entry_id": entry.id,
                "created_at": entry.created_at,
                "date_formatted": date_fmt,
                "snippet": snippet,
                "similarity_score": round(cosine_sim, 4),
                "lexical_score": round(lexical_score, 4),
                "combined_score": round(combined_score, 4)
            })

    scored_items.sort(key=lambda x: x["combined_score"], reverse=True)
    top_items = scored_items[:req.top_k]

    if not top_items:
        return RAGAskResponse(
            query=req.query,
            answer=None,
            source_entry_ids=[],
            sources=[],
            abstained=True,
            safety_route="normal",
            message="I couldn't find a related entry in your previous reflections.",
            provider=rag_service.generator_mode
        )

    # 5. Generate grounded answer
    rag_output = rag_service.generate_grounded_answer(req.query, top_items)

    source_items = [
        SearchResultItem(
            entry_id=item["entry_id"],
            created_at=item["created_at"],
            date_formatted=item["date_formatted"],
            snippet=item["snippet"],
            similarity_score=item["similarity_score"],
            lexical_score=item["lexical_score"],
            combined_score=item["combined_score"]
        )
        for item in top_items
    ]

    # 6. Validate citation contract (strict subset of valid retrieved entry IDs)
    valid_id_set = {item["entry_id"] for item in top_items}
    validated_cited_uuids = []
    for cid in rag_output["source_entry_ids"]:
        try:
            u = uuid.UUID(str(cid))
            if u in valid_id_set:
                validated_cited_uuids.append(u)
        except Exception:
            pass

    return RAGAskResponse(
        query=req.query,
        answer=rag_output["answer"],
        source_entry_ids=validated_cited_uuids,
        sources=source_items,
        abstained=rag_output["abstained"],
        safety_route=rag_output["safety_route"],
        message=rag_output["message"],
        provider=rag_service.generator_mode
    )

@router.post("/ask/feedback")
async def submit_rag_feedback(
    req: RAGFeedbackRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Record user feedback ('This doesn't sound right') without storing raw question text.
    Uses SHA-256 query hash to guarantee sensitive journal query privacy.
    """
    q_hash = rag_service.hash_query_for_privacy(req.query)
    feedback = RagFeedback(
        user_id=current_user.id,
        query_hash=q_hash,
        feedback_type=req.feedback_type
    )
    session.add(feedback)
    await session.commit()
    return {"status": "success", "message": "Feedback recorded safely."}


