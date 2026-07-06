"""
Security primitives: password hashing and JWT token management.

This module is intentionally free of database or web-framework concerns so
it can be unit tested in isolation.
"""

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    """Decoded and validated JWT payload."""

    sub: str  # subject: user id (as string)
    exp: int
    iat: int
    jti: str  # unique token id, useful for future revocation/blacklisting
    type: TokenType

    @property
    def expires_at(self) -> datetime:
        """Return the token expiration timestamp as a timezone-aware datetime."""
        return datetime.fromtimestamp(self.exp, tz=timezone.utc)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, token_type: TokenType, expires_delta: timedelta) -> str:
    """Build and sign a JWT for the given subject and token type."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": subject,
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid.uuid4()),
        "type": token_type.value,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: uuid.UUID) -> str:
    """Create a short-lived access token for the given user id."""
    settings = get_settings()
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a longer-lived refresh token for the given user id."""
    settings = get_settings()
    return _create_token(
        subject=str(user_id),
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: Optional[TokenType] = None) -> TokenPayload:
    """
    Decode and validate a JWT.

    Raises:
        TokenExpiredError: if the token has expired.
        InvalidTokenError: if the token is malformed, has an invalid
            signature, or does not match the expected token type.
    """
    settings = get_settings()
    try:
        raw_payload: dict[str, Any] = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("Token has expired.") from exc
    except JWTError as exc:
        raise InvalidTokenError("Token is invalid or malformed.") from exc

    try:
        payload = TokenPayload.model_validate(raw_payload)
    except ValidationError as exc:
        raise InvalidTokenError("Token payload is malformed.") from exc

    if expected_type is not None and payload.type != expected_type:
        raise InvalidTokenError(
            f"Expected a '{expected_type.value}' token but received a '{payload.type.value}' token."
        )

    return payload
