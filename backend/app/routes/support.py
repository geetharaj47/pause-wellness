from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import SupportResource

router = APIRouter(prefix="/api/v1/support-resources", tags=["Support Resources"])

class SupportResourceResponse(BaseModel):
    id: str
    region: str
    display_name: str
    contact: str
    type: str
    source_url: str
    verified_at: str
    language_notes: str

class SupportCatalogResponse(BaseModel):
    disclaimer: str
    region: str
    resources: List[SupportResourceResponse]

@router.get("", response_model=SupportCatalogResponse)
async def get_support_resources(
    country: str = Query("IN", description="Country code (e.g. IN)"),
    session: AsyncSession = Depends(get_session)
):
    query = select(SupportResource).where(SupportResource.region == country.upper())
    result = await session.execute(query)
    resources = result.scalars().all()

    # If no resources for requested region, default to IN
    if not resources:
        result = await session.execute(select(SupportResource).where(SupportResource.region == "IN"))
        resources = result.scalars().all()

    return SupportCatalogResponse(
        disclaimer="Pause is a self-reflection companion, NOT an emergency service or clinical crisis intervention. Pause is not actively monitored, does not contact emergency services automatically, and cannot guarantee detection. If you or someone you know needs immediate assistance, please use these verified human support lines.",
        region=country.upper(),
        resources=[
            SupportResourceResponse(
                id=r.id,
                region=r.region,
                display_name=r.display_name,
                contact=r.contact,
                type=r.type,
                source_url=r.source_url,
                verified_at=r.verified_at,
                language_notes=r.language_notes
            )
            for r in resources
        ]
    )

from app.services.crisis_service import crisis_service, CrisisDetectionResult

class SafetyCheckRequest(BaseModel):
    text: str

@router.post("/check-safety", response_model=CrisisDetectionResult)
async def check_text_safety(req: SafetyCheckRequest):
    """
    Evaluate submitted text for immediate crisis or deep distress signals.
    Strict privacy requirement: Never stores or logs the text in any database or audit log.
    """
    return crisis_service.evaluate_text(req.text)

