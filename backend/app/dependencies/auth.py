"""
FastAPI dependency providers.

Centralizes construction of repositories and services so endpoints only
need to declare a single `Depends(...)` and never instantiate concrete
classes themselves — this is our dependency-injection boundary.
"""

import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError, NotFoundError
from app.core.security import TokenType, decode_token
from app.database.session import get_db
from app.models.user import User
from app.repositories.preference_repository import (
    AIPreferenceRepository,
    NotificationPreferenceRepository,
    UserPreferenceRepository,
)
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.preference_service import (
    AIPreferenceService,
    NotificationPreferenceService,
    UserPreferenceService,
)
from app.services.user_service import UserService

_bearer_scheme = HTTPBearer(auto_error=False)


# --- Repository dependencies ---


def get_user_repository(session: Annotated[AsyncSession, Depends(get_db)]) -> UserRepository:
    return UserRepository(session)


def get_revoked_token_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> RevokedTokenRepository:
    return RevokedTokenRepository(session)


def get_user_preference_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> UserPreferenceRepository:
    return UserPreferenceRepository(session)


def get_ai_preference_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AIPreferenceRepository:
    return AIPreferenceRepository(session)


def get_notification_preference_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationPreferenceRepository:
    return NotificationPreferenceRepository(session)


# --- Service dependencies ---


def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(
        user_repository=user_repository,
        revoked_token_repository=revoked_token_repository,
        access_token_expire_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


def get_user_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repository)


def get_user_preference_service(
    preference_repository: Annotated[UserPreferenceRepository, Depends(get_user_preference_repository)],
) -> UserPreferenceService:
    return UserPreferenceService(preference_repository)


def get_ai_preference_service(
    ai_preference_repository: Annotated[AIPreferenceRepository, Depends(get_ai_preference_repository)],
) -> AIPreferenceService:
    return AIPreferenceService(ai_preference_repository)


def get_notification_preference_service(
    notification_preference_repository: Annotated[
        NotificationPreferenceRepository,
        Depends(get_notification_preference_repository),
    ],
) -> NotificationPreferenceService:
    return NotificationPreferenceService(notification_preference_repository)


# --- Auth resolvers ---


async def get_current_bearer_credentials(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> HTTPAuthorizationCredentials:
    """Return bearer credentials or raise the standard authentication error."""
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials.")
    return credentials


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(get_current_bearer_credentials)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    revoked_token_repository: Annotated[
        RevokedTokenRepository,
        Depends(get_revoked_token_repository),
    ],
) -> User:
    """
    Resolve the authenticated user from the `Authorization: Bearer <token>`
    header. Used as a dependency on any endpoint that requires
    authentication.

    Raises:
        AuthenticationError: if the header is missing, the token is
            invalid/expired, or the token is not an access token.
        NotFoundError: if the token is valid but the user no longer exists.
    """
    if credentials is None:
        raise AuthenticationError("Missing authentication credentials.")

    payload = decode_token(credentials.credentials, expected_type=TokenType.ACCESS)
    if await revoked_token_repository.exists(payload.jti):
        raise AuthenticationError("Token has been revoked.")

    user = await user_repository.get_by_id(uuid.UUID(payload.sub))
    if user is None:
        raise NotFoundError("The account associated with this token no longer exists.")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated.")

    return user


CurrentBearerCredentials = Annotated[
    HTTPAuthorizationCredentials,
    Depends(get_current_bearer_credentials),
]
CurrentUser = Annotated[User, Depends(get_current_user)]
