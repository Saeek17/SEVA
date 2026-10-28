import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Any
from cryptography.fernet import Fernet
from passlib.context import CryptContext
from jose import jwt

from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _get_fernet() -> Fernet:
    """Ensure key is properly padded/formatted for Fernet."""
    raw_key = settings.ENCRYPTION_KEY
    if not raw_key:
        raw_key = "rV2wYpE8Z6tX0cM3vB1nK7jH5fD4sA9qL2wE5rT8yU1="
    # Ensure standard base64 32 bytes
    key_bytes = raw_key.encode("utf-8")
    if len(key_bytes) != 44:
        # Generate deterministic 32-byte urlsafe base64 key from the input
        digest = hashlib.sha256(key_bytes).digest()
        key_bytes = base64.urlsafe_b64encode(digest)
    return Fernet(key_bytes)

def encrypt_phone(phone: str) -> str:
    """Encrypt phone number for storage at rest."""
    if not phone:
        return ""
    f = _get_fernet()
    return f.encrypt(phone.strip().encode("utf-8")).decode("utf-8")

def decrypt_phone(encrypted_phone: str) -> str:
    """Decrypt phone number from database storage."""
    if not encrypted_phone:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_phone.encode("utf-8")).decode("utf-8")
    except Exception:
        # Return masked or empty if decryption fails (e.g. key change)
        return "[ENCRYPTION_ERROR]"

def hash_phone(phone: str) -> str:
    """Deterministic HMAC-SHA256 hash for exact-match indexing without decryption."""
    if not phone:
        return ""
    clean = phone.strip()
    return hmac.new(settings.SECRET_KEY.encode("utf-8"), clean.encode("utf-8"), hashlib.sha256).hexdigest()

def mask_phone(phone: str) -> str:
    """Display phone with masked central digits for privacy (e.g., +91 98****3210)."""
    if not phone:
        return ""
    s = phone.strip()
    if len(s) <= 4:
        return s
    prefix_len = 3 if s.startswith("+") else 2
    suffix_len = 4
    if len(s) <= prefix_len + suffix_len:
        return s[:2] + "****" + s[-2:]
    masked_middle = "*" * (len(s) - prefix_len - suffix_len)
    return s[:prefix_len] + masked_middle + s[-suffix_len:]

# JWT & Password Helpers
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None
