from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete

from app.database import get_session
from app.models import User, ConsentRecord, AuditEvent, EntryEmbedding
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/consents", tags=["Consent Management"])

class ConsentStatusResponse(BaseModel):
    save_journal: bool
    emotion_analysis: bool
    embeddings_rag: bool
    external_inference: bool
    policy_version: str
    updated_at: Optional[datetime]

class ConsentUpdateRequest(BaseModel):
    save_journal: Optional[bool] = None
    emotion_analysis: Optional[bool] = None
    embeddings_rag: Optional[bool] = None
    external_inference: Optional[bool] = None
    # If true and embeddings_rag is set to False, immediately delete existing embeddings
    delete_existing_embeddings_on_revoke: bool = True

@router.get("", response_model=ConsentStatusResponse)
async def get_consents(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(ConsentRecord).where(ConsentRecord.user_id == current_user.id)
    )
    records = result.scalars().all()
    
    status_map = {
        "save_journal": False,
        "emotion_analysis": False,
        "embeddings_rag": False,
        "external_inference": False
    }
    latest_update = None
    for r in records:
        if r.purpose in status_map:
            status_map[r.purpose] = r.granted
            if r.granted_at and (latest_update is None or r.granted_at > latest_update):
                latest_update = r.granted_at
            if r.revoked_at and (latest_update is None or r.revoked_at > latest_update):
                latest_update = r.revoked_at

    return ConsentStatusResponse(
        save_journal=status_map["save_journal"],
        emotion_analysis=status_map["emotion_analysis"],
        embeddings_rag=status_map["embeddings_rag"],
        external_inference=status_map["external_inference"],
        policy_version="1.0",
        updated_at=latest_update
    )

@router.put("", response_model=ConsentStatusResponse)
async def update_consents(
    req: ConsentUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    now = datetime.utcnow()
    purposes = {
        "save_journal": req.save_journal,
        "emotion_analysis": req.emotion_analysis,
        "embeddings_rag": req.embeddings_rag,
        "external_inference": req.external_inference,
    }

    for purpose, granted in purposes.items():
        if granted is None:
            continue
        
        result = await session.execute(
            select(ConsentRecord).where(
                ConsentRecord.user_id == current_user.id,
                ConsentRecord.purpose == purpose
            )
        )
        record = result.scalars().first()
        if not record:
            record = ConsentRecord(
                user_id=current_user.id,
                purpose=purpose,
                policy_version="1.0",
                granted=granted,
                granted_at=now if granted else None,
                revoked_at=None if granted else now
            )
            session.add(record)
        else:
            if record.granted != granted:
                record.granted = granted
                if granted:
                    record.granted_at = now
                    record.revoked_at = None
                else:
                    record.revoked_at = now

        # If user explicitly revoked embeddings_rag and opted to purge existing embeddings
        if purpose == "embeddings_rag" and granted is False and req.delete_existing_embeddings_on_revoke:
            await session.execute(
                delete(EntryEmbedding).where(EntryEmbedding.user_id == current_user.id)
            )

    # Log audit event for consent change
    session.add(AuditEvent(
        user_id=current_user.id,
        action="CONSENT_UPDATE",
        timestamp=now,
        status="SUCCESS",
        client_ip=request.client.host if request.client else None
    ))

    await session.commit()
    return await get_consents(current_user=current_user, session=session)
