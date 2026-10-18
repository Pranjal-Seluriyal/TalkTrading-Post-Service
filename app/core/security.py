from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import bcrypt
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> int:
    """
    Decodes the JWT token and extracts the authenticated canonical integer user_id.
    Validates token signature, expiration, and identity claims.
    Accepts:
    1. 'user_id' claim if present as integer or digit string.
    2. 'sub' claim if present as integer or digit string.
    3. If 'sub' is a UUID string and 'user_id' is not present, derives a deterministic
       canonical integer ID from UUID or queries/maps if available, or rejects with 401 if invalid.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # 1. First check explicit user_id
        user_id_val = payload.get("user_id")
        if user_id_val is not None:
            try:
                return int(user_id_val)
            except (ValueError, TypeError):
                pass

        # 2. Check sub claim
        sub_val = payload.get("sub")
        if sub_val is None:
            raise credentials_exception

        try:
            return int(sub_val)
        except (ValueError, TypeError):
            # sub might be a UUID string
            try:
                u = uuid.UUID(str(sub_val))
                # Derive deterministic 31-bit positive integer from UUID
                return int(u.int & 0x7FFFFFFF)
            except (ValueError, TypeError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token sub/user_id claim must be a valid canonical integer or UUID",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    except JWTError:
        raise credentials_exception


def get_optional_user_id(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[int]:
    """
    Optional authentication helper for endpoints that allow public reads with optional personalized flags.
    """
    if not token:
        return None
    try:
        return get_current_user_id(token)
    except HTTPException:
        return None


def get_current_user(
    user_id: int = Depends(get_current_user_id),
):
    """Legacy helper returning a dummy/resolved User instance from authenticated user_id."""
    from app.models.user import User
    # Returns object with id attribute compatible with both dict and model interfaces
    return User(id=user_id, user_uuid=str(user_id), username=f"user_{user_id}", email=f"user_{user_id}@talktrading.com", hashed_password="")