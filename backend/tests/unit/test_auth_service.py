"""
Unit tests for `AuthService`.

Uses a lightweight fake `UserRepository` (not a real database) so these
tests exercise pure business logic in isolation and run fast.
"""

import uuid
from typing import Optional

import pytest

from app.services.auth_service import AuthService
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from app.core.security import TokenType, create_refresh_token, decode_token, hash_password
from app.schemas.user import UserCreate
from app.models.user import User


class FakeUserRepository:
    """An in-memory stand-in for `UserRepository`, sufficient for unit testing services."""

    def __init__(self):
        self._users: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email.lower():
                return user
        return None

    async def create(self, *, email: str, full_name: str, hashed_password: str) -> User:
        user = User(
            id=uuid.uuid4(),
            email=email.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=False,
            is_verified=False,
            subscription_status="pending",
        )
        self._users[user.id] = user
        return user

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            if value is not None:
                setattr(user, key, value)
        return user


class FakeRevokedTokenRepository:
    """An in-memory stand-in for revoked token persistence."""

    def __init__(self):
        self._revoked: set[str] = set()

    async def exists(self, jti: str) -> bool:
        return jti in self._revoked

    async def revoke(self, *, jti: str, user_id: uuid.UUID, token_type: str, expires_at):
        self._revoked.add(jti)
        return None


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(
        user_repository=FakeUserRepository(),
        revoked_token_repository=FakeRevokedTokenRepository(),
        access_token_expire_minutes=30,
    )


class TestRegister:
    async def test_register_creates_user_and_returns_user(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)

        assert user.email == "jane@example.com"
        assert user.is_active is False
        assert user.subscription_status == "pending"

    async def test_register_rejects_duplicate_email(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        await auth_service.register(payload)

        with pytest.raises(ConflictError):
            await auth_service.register(payload)

    async def test_registered_password_is_hashed_not_stored_in_plaintext(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        assert user.hashed_password != "StrongPass1"


class TestAuthenticate:
    async def test_authenticate_succeeds_with_correct_credentials(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)

        user, tokens = await auth_service.authenticate("jane@example.com", "StrongPass1")
        assert user.email == "jane@example.com"
        assert tokens.access_token

    async def test_authenticate_fails_with_wrong_password(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        await auth_service.register(payload)

        with pytest.raises(AuthenticationError):
            await auth_service.authenticate("jane@example.com", "WrongPassword1")

    async def test_authenticate_fails_for_unknown_email(self, auth_service: AuthService):
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate("nobody@example.com", "whatever")

    async def test_authenticate_fails_for_deactivated_account(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = False
        await auth_service._users.update(user)

        with pytest.raises(AuthenticationError):
            await auth_service.authenticate("jane@example.com", "StrongPass1")

    async def test_authenticate_fails_for_pending_subscription(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        await auth_service.register(payload)

        with pytest.raises(AuthenticationError):
            await auth_service.authenticate("jane@example.com", "StrongPass1")


class TestRefresh:
    async def test_refresh_issues_new_token_pair(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)
        _, tokens = await auth_service.authenticate("jane@example.com", "StrongPass1")

        new_tokens = await auth_service.refresh(tokens.refresh_token)
        assert new_tokens.access_token != tokens.access_token
        assert new_tokens.refresh_token != tokens.refresh_token

    async def test_refresh_rejects_reused_refresh_token(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)
        _, tokens = await auth_service.authenticate("jane@example.com", "StrongPass1")

        await auth_service.refresh(tokens.refresh_token)

        with pytest.raises(AuthenticationError):
            await auth_service.refresh(tokens.refresh_token)

    async def test_refresh_rejects_access_token_used_as_refresh_token(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)
        _, tokens = await auth_service.authenticate("jane@example.com", "StrongPass1")

        with pytest.raises(Exception):
            await auth_service.refresh(tokens.access_token)

    async def test_refresh_fails_for_nonexistent_user(self, auth_service: AuthService):
        orphan_refresh_token = create_refresh_token(uuid.uuid4())
        with pytest.raises(NotFoundError):
            await auth_service.refresh(orphan_refresh_token)


class TestLogout:
    async def test_logout_revokes_access_token(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)
        _, tokens = await auth_service.authenticate("jane@example.com", "StrongPass1")
        decoded = decode_token(tokens.access_token, expected_type=TokenType.ACCESS)

        await auth_service.logout(tokens.access_token)

        assert await auth_service._revoked_tokens.exists(decoded.jti)


class TestChangePassword:
    async def test_change_password_updates_hash(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)
        _, tokens = await auth_service.authenticate("jane@example.com", "StrongPass1")

        await auth_service.change_password(user.id, "StrongPass1", "NewStrongPass2")

        with pytest.raises(AuthenticationError):
            await auth_service.authenticate("jane@example.com", "StrongPass1")
        _user, tokens = await auth_service.authenticate("jane@example.com", "NewStrongPass2")
        assert tokens.access_token

    async def test_change_password_rejects_wrong_current_password(self, auth_service: AuthService):
        payload = UserCreate(email="jane@example.com", full_name="Jane Doe", password="StrongPass1")
        user = await auth_service.register(payload)
        user.is_active = True
        user.subscription_status = "active"
        await auth_service._users.update(user)

        with pytest.raises(AuthenticationError):
            await auth_service.change_password(user.id, "WrongPassword1", "NewStrongPass2")
