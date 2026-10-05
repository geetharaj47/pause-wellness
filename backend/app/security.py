import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from cryptography.fernet import Fernet
from jose import JWTError, jwt
from app.config import settings

# Initialize Fernet cipher for application-level envelope encryption of journal text
_fernet_key = settings.PAUSE_JOURNAL_ENCRYPTION_KEY.encode()
try:
    _cipher_suite = Fernet(_fernet_key)
except Exception:
    # Fallback to deterministic key if corrupted in dev
    _cipher_suite = Fernet(Fernet.generate_key())

def encrypt_journal_text(plain_text: str) -> str:
    """Encrypt sensitive journal content before writing to database."""
    if not plain_text:
        return ""
    encrypted_bytes = _cipher_suite.encrypt(plain_text.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_journal_text(encrypted_text: str) -> str:
    """Decrypt sensitive journal content only for the authenticated owner."""
    if not encrypted_text:
        return ""
    try:
        decrypted_bytes = _cipher_suite.decrypt(encrypted_text.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except Exception:
        # If decryption fails (e.g. legacy plain text), return safe fallback or empty
        return "[Encrypted text could not be decrypted]"

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte salt."""
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
    """Create signed JWT bearer token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate signed JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
