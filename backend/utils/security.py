from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from config.settings import settings
import logging
import hashlib
import secrets

logger = logging.getLogger(__name__)

# Use simple but secure PBKDF2-based hashing (no external dependency issues)
HASH_METHOD = "pbkdf2_sha256"
HASH_ITERATIONS = 100000

def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256
    Format: pbkdf2_sha256$iterations$salt$hash
    """
    try:
        salt = secrets.token_hex(32)  # 64-character hex salt (32 bytes)
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            HASH_ITERATIONS
        )
        hashed = f"{HASH_METHOD}${HASH_ITERATIONS}${salt}${hash_obj.hex()}"
        logger.info(f"Password hashed successfully with PBKDF2")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError(f"Unable to hash password: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    try:
        # Parse the hash format: pbkdf2_sha256$iterations$salt$hash
        if not hashed_password.startswith('pbkdf2_sha256$'):
            logger.warning(f"Unknown hash format")
            return False
        
        parts = hashed_password.split('$')
        if len(parts) != 4:
            logger.warning(f"Invalid hash format: {len(parts)} parts")
            return False
        
        method, iterations_str, salt, stored_hash = parts
        iterations = int(iterations_str)
        
        # Recompute hash with provided password
        hash_obj = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            iterations
        )
        computed_hash = hash_obj.hex()
        
        # Constant-time comparison to avoid timing attacks
        result = secrets.compare_digest(computed_hash, stored_hash)
        
        if not result:
            logger.info("Password verification failed - mismatch")
        
        return result
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None

def verify_access_token(token: str) -> Optional[dict]:
    """Verify an access token (must have type='access')"""
    payload = verify_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None

def verify_refresh_token(token: str) -> Optional[dict]:
    """Verify a refresh token (must have type='refresh')"""
    payload = verify_token(token)
    if payload and payload.get("type") == "refresh":
        return payload
    return None
