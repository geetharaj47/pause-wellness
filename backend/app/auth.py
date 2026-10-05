import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models import User, ConsentRecord, AuditEvent
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# ==========================================
# SCHEMAS
# ==========================================

class RegisterRequest(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    confirmed_18_plus: bool = Field(..., description="Confirmation that user is 18 or older")
    locale: str = "en-IN"
    selected_country: str = "IN"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str
    selected_country: str
    confirmed_18_plus: bool

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime
    locale: str
    selected_country: str
    confirmed_18_plus: bool
    is_demo_account: bool

# ==========================================
# AUTH DEPENDENCY
# ==========================================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = await session.get(User, user_uuid)
    if user is None:
        raise credentials_exception
    return user

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    # Enforce 18+ policy per project specification
    if not req.confirmed_18_plus:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pause is designed for university students aged 18 and older. Confirmation is required."
        )

    # Check for existing account
    existing = await session.execute(select(User).where(User.email == req.email.lower()))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Create user
    now = datetime.utcnow()
    new_user = User(
        email=req.email.lower(),
        password_hash=hash_password(req.password),
        created_at=now,
        locale=req.locale,
        selected_country=req.selected_country,
        confirmed_18_plus=True,
        is_demo_account=False
    )
    session.add(new_user)
    await session.flush() # generate user.id

    # Initialize default granular consent records per specification:
    # 1. save_journal: True (default opt-in with explicit notice)
    # 2. emotion_analysis: False (requires explicit action/consent)
    # 3. embeddings_rag: False (requires explicit opt-in)
    # 4. external_inference: False (always default off per spec)
    default_consents = [
        ConsentRecord(user_id=new_user.id, purpose="save_journal", granted=True, granted_at=now),
        ConsentRecord(user_id=new_user.id, purpose="emotion_analysis", granted=False),
        ConsentRecord(user_id=new_user.id, purpose="embeddings_rag", granted=False),
        ConsentRecord(user_id=new_user.id, purpose="external_inference", granted=False),
    ]
    for c in default_consents:
        session.add(c)

    # Log security audit event (no private text)
    session.add(AuditEvent(
        user_id=new_user.id,
        action="AUTH_REGISTER",
        timestamp=now,
        status="SUCCESS",
        client_ip=request.client.host if request.client else None
    ))

    await session.commit()
    await session.refresh(new_user)

    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        email=new_user.email,
        selected_country=new_user.selected_country,
        confirmed_18_plus=new_user.confirmed_18_plus
    )

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(select(User).where(User.email == req.email.lower()))
    user = result.scalars().first()

    if not user or not verify_password(req.password, user.password_hash):
        session.add(AuditEvent(
            user_id=user.id if user else None,
            action="AUTH_LOGIN",
            timestamp=datetime.utcnow(),
            status="FAILURE",
            client_ip=request.client.host if request.client else None
        ))
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    session.add(AuditEvent(
        user_id=user.id,
        action="AUTH_LOGIN",
        timestamp=datetime.utcnow(),
        status="SUCCESS",
        client_ip=request.client.host if request.client else None
    ))
    await session.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        selected_country=user.selected_country,
        confirmed_18_plus=user.confirmed_18_plus
    )

@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    session.add(AuditEvent(
        user_id=current_user.id,
        action="AUTH_LOGOUT",
        timestamp=datetime.utcnow(),
        status="SUCCESS",
        client_ip=request.client.host if request.client else None
    ))
    await session.commit()
    return {"message": "Successfully logged out."}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        locale=current_user.locale,
        selected_country=current_user.selected_country,
        confirmed_18_plus=current_user.confirmed_18_plus,
        is_demo_account=current_user.is_demo_account
    )
