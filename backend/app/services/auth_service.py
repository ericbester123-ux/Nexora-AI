"""
Authentication application service.

Contains the business logic for registering users, authenticating
credentials, and issuing/refreshing JWT tokens. Depends only on the
`UserRepository` abstraction and security primitives — never on FastAPI or
raw SQLAlchemy sessions directly, so it can be unit tested with a fake
repository.
"""

import logging
import uuid

from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    InvalidTokenError,
    NotFoundError,
)
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.schemas.auth import TokenResponse
from app.schemas.user import UserCreate
from app.models.user import User
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Encapsulates all authentication-related business rules."""

    def __init__(
        self,
        user_repository: UserRepository,
        revoked_token_repository: RevokedTokenRepository,
        access_token_expire_minutes: int,
    ):
        self._users = user_repository
        self._revoked_tokens = revoked_token_repository
        self._access_token_expire_minutes = access_token_expire_minutes

    async def register(self, payload: UserCreate) -> User:
        """
        Register a new user.

        Raises:
            ConflictError: if a user with the given email already exists.
        """
        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            logger.info("Registration attempt with already-registered email.", extra={
                "event": "registration_conflict",
            })
            raise ConflictError("An account with this email already exists.")

        user = await self._users.create(
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
        )
        logger.info("New user registered.", extra={"event": "user_registered", "user_id": str(user.id)})

        return user

    async def authenticate(self, email: str, password: str) -> tuple[User, TokenResponse]:
        """
        Validate credentials and issue a new token pair.

        Raises:
            AuthenticationError: if the email is unknown, the password is
                wrong, or the account has been deactivated. The same generic
                error is used in all cases to avoid leaking which emails are
                registered (user enumeration protection).
        """
        user = await self._users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            logger.warning("Failed login attempt.", extra={"event": "login_failed"})
            raise AuthenticationError("Incorrect email or password.")

        if not user.is_active:
            logger.warning("Login attempt on deactivated account.", extra={
                "event": "login_deactivated_account", "user_id": str(user.id),
            })
            raise AuthenticationError("This account has been deactivated.")

        logger.info("User authenticated.", extra={"event": "login_success", "user_id": str(user.id)})
        tokens = self._issue_tokens(user.id)
        return user, tokens

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """
        Exchange a valid refresh token for a new token pair.

        Raises:
            InvalidTokenError / TokenExpiredError: if the refresh token is
                invalid, expired, or not a refresh-type token.
            NotFoundError: if the associated user no longer exists.
            AuthenticationError: if the associated account is deactivated.
        """
        payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        if await self._revoked_tokens.exists(payload.jti):
            raise InvalidTokenError("Token has been revoked.")

        user_id = uuid.UUID(payload.sub)

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("The account associated with this token no longer exists.")
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")

        logger.info("Access token refreshed.", extra={"event": "token_refreshed", "user_id": str(user.id)})
        await self._revoked_tokens.revoke(
            jti=payload.jti,
            user_id=user.id,
            token_type=payload.type.value,
            expires_at=payload.expires_at,
        )
        return self._issue_tokens(user.id)

    async def logout(self, access_token: str, refresh_token: str | None = None) -> None:
        """
        Revoke the presented access token and, when provided, its refresh token.

        This gives stateless JWT logout concrete server-side effect without
        requiring a session table.
        """
        access_payload = decode_token(access_token, expected_type=TokenType.ACCESS)
        user_id = uuid.UUID(access_payload.sub)
        await self._revoked_tokens.revoke(
            jti=access_payload.jti,
            user_id=user_id,
            token_type=access_payload.type.value,
            expires_at=access_payload.expires_at,
        )

        if refresh_token is None:
            logger.info("User logged out.", extra={"event": "logout", "user_id": str(user_id)})
            return

        refresh_payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        if refresh_payload.sub != access_payload.sub:
            raise AuthenticationError("Refresh token does not belong to the authenticated user.")

        await self._revoked_tokens.revoke(
            jti=refresh_payload.jti,
            user_id=user_id,
            token_type=refresh_payload.type.value,
            expires_at=refresh_payload.expires_at,
        )
        logger.info("User logged out.", extra={"event": "logout", "user_id": str(user_id)})

    async def change_password(
        self,
        user_id: uuid.UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password after verifying their current password.

        Raises:
            AuthenticationError: if the current password is incorrect.
            BadRequestError: if the new password matches the current password.
            NotFoundError: if the user no longer exists.
        """
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        if not verify_password(current_password, user.hashed_password):
            logger.warning(
                "Password change failed due to invalid current password.",
                extra={"event": "password_change_failed", "user_id": str(user.id)},
            )
            raise AuthenticationError("Current password is incorrect.")
        if verify_password(new_password, user.hashed_password):
            raise BadRequestError("New password must be different from the current password.")

        await self._users.update(user, hashed_password=hash_password(new_password))
        logger.info("User password changed.", extra={"event": "password_changed", "user_id": str(user.id)})

    def _issue_tokens(self, user_id: uuid.UUID) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id),
            refresh_token=create_refresh_token(user_id),
            expires_in=self._access_token_expire_minutes * 60,
        )
