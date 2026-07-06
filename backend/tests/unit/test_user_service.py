"""
Unit tests for UserService.
"""

import uuid

import pytest
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.schemas.user import UserProfileUpdate
from app.services.user_service import UserService


class FakeUserRepository:
    def __init__(self):
        self._users: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._users.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
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
            is_active=True,
            is_verified=False,
        )
        self._users[user.id] = user
        return user

    async def update(self, user: User, **fields) -> User:
        for key, value in fields.items():
            setattr(user, key, value)
        return user


@pytest.fixture
def user_service() -> UserService:
    return UserService(user_repository=FakeUserRepository())


@pytest.fixture
async def existing_user(user_service: UserService) -> User:
    user = User(
        id=uuid.uuid4(),
        email="jane@example.com",
        full_name="Jane Doe",
        hashed_password="hashed",
        is_active=True,
        is_verified=True,
    )
    user_service._users._users[user.id] = user
    return user


class TestGetProfile:
    async def test_get_profile_returns_user(self, user_service: UserService, existing_user: User):
        result = await user_service.get_profile(existing_user.id)
        assert result.id == existing_user.id
        assert result.email == existing_user.email

    async def test_get_profile_raises_not_found_for_missing_user(self, user_service: UserService):
        with pytest.raises(NotFoundError):
            await user_service.get_profile(uuid.uuid4())


class TestUpdateProfile:
    async def test_update_profile_sets_all_fields(self, user_service: UserService, existing_user: User):
        payload = UserProfileUpdate(
            first_name="Jane",
            last_name="Smith",
            display_name="Jane S",
            timezone="America/New_York",
            country="US",
            preferred_currency="USD",
            profile_photo_url="https://example.com/photo.jpg",
            biography="A developer.",
            portfolio_url="https://example.com/portfolio",
            years_of_experience=10,
            primary_skills=["Python", "FastAPI"],
            secondary_skills=["React", "Docker"],
        )
        result = await user_service.update_profile(existing_user.id, payload)

        assert result.first_name == "Jane"
        assert result.last_name == "Smith"
        assert result.display_name == "Jane S"
        assert result.timezone == "America/New_York"
        assert result.country == "US"
        assert result.preferred_currency == "USD"
        assert result.profile_photo_url == "https://example.com/photo.jpg"
        assert result.biography == "A developer."
        assert result.portfolio_url == "https://example.com/portfolio"
        assert result.years_of_experience == 10
        assert result.primary_skills == ["Python", "FastAPI"]
        assert result.secondary_skills == ["React", "Docker"]

    async def test_update_profile_with_empty_payload_does_not_change_anything(
        self, user_service: UserService, existing_user: User
    ):
        payload = UserProfileUpdate()
        result = await user_service.update_profile(existing_user.id, payload)
        assert result.first_name is None
        assert result.years_of_experience is None

    async def test_update_profile_partial_update(self, user_service: UserService, existing_user: User):
        payload = UserProfileUpdate(years_of_experience=5)
        result = await user_service.update_profile(existing_user.id, payload)
        assert result.years_of_experience == 5
        assert result.first_name is None  # not set

    async def test_update_profile_raises_not_found_for_missing_user(
        self, user_service: UserService
    ):
        payload = UserProfileUpdate(first_name="Ghost")
        with pytest.raises(NotFoundError):
            await user_service.update_profile(uuid.uuid4(), payload)
