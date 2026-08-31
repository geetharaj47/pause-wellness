import uuid
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.config import settings
from app.database import get_session
from app.models import User, ConsentRecord, UserPreference

# OAuth2 scheme for token retrieval
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Router setup
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================

class UserRegister(BaseModel):
    email: str = Field(..., description="Unique email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    timezone: str = Field(default="UTC", description="Preferred timezone")


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str


class ConsentSubmit(BaseModel):
    consent_given: bool
    consent_version: str = "1.0"


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime
    timezone: str
    has_consented: bool


# ==========================================
# CRYPTOGRAPHY UTILITIES (PBKDF2 HMAC SHA256)
# ==========================================

def hash_password(password: str) -> str:
    """Hash password using standard PBKDF2-HMAC-SHA256 with a 16-byte salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        iterations=100000
    )
    return f"{salt.hex()}:{pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password by rebuilding the PBKDF2 hash using the stored salt."""
    try:
        salt_hex, hash_hex = hashed_password.split(':')
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        actual_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt,
            iterations=100000
        )
        return actual_hash == expected_hash
    except Exception:
        return False



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# ==========================================
# AUTHENTICATION DEPENDENCY
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
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = await session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user


# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegister,
    session: AsyncSession = Depends(get_session)
):
    # Check if user already exists
    stmt = select(User).where(User.email == payload.email.strip().lower())
    result = await session.execute(stmt)
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email is already registered."
        )

    # Create new User
    hashed_pwd = hash_password(payload.password)
    new_user = User(
        email=payload.email.strip().lower(),
        password_hash=hashed_pwd,
        timezone=payload.timezone
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    # Initialize empty preferences
    preferences = UserPreference(user_id=new_user.id)
    session.add(preferences)
    await session.commit()

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(new_user.id)})
    return TokenResponse(
        access_token=access_token,
        user_id=new_user.id,
        email=new_user.email
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    session: AsyncSession = Depends(get_session)
):
    stmt = select(User).where(User.email == payload.email.strip().lower())
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    # Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email
    )


@router.post("/consent", status_code=status.HTTP_200_OK)
async def log_consent(
    payload: ConsentSubmit,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Log consent action in database
    consent_record = ConsentRecord(
        user_id=current_user.id,
        consent_given=payload.consent_given,
        consent_version=payload.consent_version
    )
    session.add(consent_record)
    await session.commit()
    return {"message": "Consent record successfully saved."}


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # Query check if consent was logged
    stmt = select(ConsentRecord).where(
        ConsentRecord.user_id == current_user.id,
        ConsentRecord.consent_given == True
    ).order_by(ConsentRecord.timestamp.desc())
    result = await session.execute(stmt)
    consent = result.scalar_one_or_none()
    
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at,
        timezone=current_user.timezone,
        has_consented=consent is not None
    )
