"""
Unit tests for preference services.
"""

import uuid

import pytest
from app.models.ai_preference import AIPreference
from app.models.notification_preference import NotificationPreference
from app.models.user_preference import UserPreference
from app.schemas.preferences import (
    AIPreferencesUpdate,
    NotificationPreferencesUpdate,
    UserPreferencesUpdate,
)
from app.services.preference_service import (
    AIPreferenceService,
    NotificationPreferenceService,
    UserPreferenceService,
)


class FakeUserPreferenceRepository:
    def __init__(self):
        self._prefs: dict[uuid.UUID, UserPreference] = {}

    async def get_by_user_id(self, user_id):
        return self._prefs.get(user_id)

    async def upsert(self, user_id, **fields):
        existing = self._prefs.get(user_id)
        if existing:
            for k, v in fields.items():
                if v is not None:
                    setattr(existing, k, v)
            return existing
        pref = UserPreference(user_id=user_id, **{k: v for k, v in fields.items() if v is not None})
        pref.id = uuid.uuid4()
        self._prefs[user_id] = pref
        return pref


class FakeAIPreferenceRepository:
    def __init__(self):
        self._prefs: dict[uuid.UUID, AIPreference] = {}

    async def get_by_user_id(self, user_id):
        return self._prefs.get(user_id)

    async def upsert(self, user_id, **fields):
        existing = self._prefs.get(user_id)
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            return existing
        pref = AIPreference(user_id=user_id, **{k: v for k, v in fields.items() if v is not None})
        pref.id = uuid.uuid4()
        self._prefs[user_id] = pref
        return pref


class FakeNotificationPreferenceRepository:
    def __init__(self):
        self._prefs: dict[uuid.UUID, NotificationPreference] = {}

    async def get_by_user_id(self, user_id):
        return self._prefs.get(user_id)

    async def upsert(self, user_id, **fields):
        existing = self._prefs.get(user_id)
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            return existing
        pref = NotificationPreference(
            user_id=user_id, **{k: v for k, v in fields.items() if v is not None}
        )
        pref.id = uuid.uuid4()
        self._prefs[user_id] = pref
        return pref


@pytest.fixture
def user_pref_service() -> UserPreferenceService:
    return UserPreferenceService(FakeUserPreferenceRepository())


@pytest.fixture
def ai_pref_service() -> AIPreferenceService:
    return AIPreferenceService(FakeAIPreferenceRepository())


@pytest.fixture
def notification_pref_service() -> NotificationPreferenceService:
    return NotificationPreferenceService(FakeNotificationPreferenceRepository())


class TestUserPreferenceService:
    async def test_get_returns_default_preferences_when_none_exist(
        self, user_pref_service: UserPreferenceService
    ):
        user_id = uuid.uuid4()
        pref = await user_pref_service.get(user_id)
        assert pref.user_id == user_id

    async def test_get_returns_existing_preferences(self, user_pref_service: UserPreferenceService):
        user_id = uuid.uuid4()
        await user_pref_service._repo.upsert(
            user_id, min_budget=100, max_budget=5000, max_daily_recommendations=5
        )
        pref = await user_pref_service.get(user_id)
        assert float(pref.min_budget) == 100
        assert float(pref.max_budget) == 5000
        assert pref.max_daily_recommendations == 5

    async def test_update_saves_all_fields(self, user_pref_service: UserPreferenceService):
        user_id = uuid.uuid4()
        payload = UserPreferencesUpdate(
            min_budget=200,
            max_budget=10000,
            preferred_categories=["Web Dev", "Mobile"],
            preferred_technologies=["Python", "React"],
            preferred_countries=["US", "GB"],
            preferred_languages=["en"],
            min_client_rating=4.0,
            require_payment_verified=True,
            max_competition_level=50,
            max_daily_recommendations=15,
            preferred_project_age="recent",
            preferred_delivery_time="flexible",
        )
        pref = await user_pref_service.update(user_id, payload)
        assert float(pref.min_budget) == 200
        assert float(pref.max_budget) == 10000
        assert pref.preferred_categories == ["Web Dev", "Mobile"]
        assert pref.require_payment_verified is True
        assert pref.max_daily_recommendations == 15

    async def test_update_partial_merge(self, user_pref_service: UserPreferenceService):
        user_id = uuid.uuid4()
        await user_pref_service._repo.upsert(user_id, min_budget=100, max_budget=5000)
        payload = UserPreferencesUpdate(max_budget=7500)
        pref = await user_pref_service.update(user_id, payload)
        assert float(pref.min_budget) == 100
        assert float(pref.max_budget) == 7500


class TestAIPreferenceService:
    async def test_get_returns_defaults_when_none_exist(self, ai_pref_service: AIPreferenceService):
        user_id = uuid.uuid4()
        pref = await ai_pref_service.get(user_id)
        assert pref.user_id == user_id

    async def test_update_saves_all_fields(self, ai_pref_service: AIPreferenceService):
        user_id = uuid.uuid4()
        payload = AIPreferencesUpdate(
            ai_enabled=True,
            proposal_tone="friendly",
            proposal_length="short",
            writing_style="persuasive",
            automatically_include_portfolio=False,
            confidence_threshold=0.85,
            bid_recommendation_style="aggressive",
            ai_learning_enabled=False,
        )
        pref = await ai_pref_service.update(user_id, payload)
        assert pref.ai_enabled is True
        assert pref.proposal_tone == "friendly"
        assert pref.proposal_length == "short"
        assert pref.writing_style == "persuasive"
        assert pref.automatically_include_portfolio is False
        assert pref.confidence_threshold == 0.85
        assert pref.bid_recommendation_style == "aggressive"
        assert pref.ai_learning_enabled is False


class TestNotificationPreferenceService:
    async def test_get_returns_defaults_when_none_exist(
        self, notification_pref_service: NotificationPreferenceService
    ):
        user_id = uuid.uuid4()
        pref = await notification_pref_service.get(user_id)
        assert pref.user_id == user_id

    async def test_update_saves_all_fields(
        self, notification_pref_service: NotificationPreferenceService
    ):
        user_id = uuid.uuid4()
        payload = NotificationPreferencesUpdate(
            push_enabled=True,
            email_enabled=False,
            high_confidence_projects=True,
            new_opportunities=False,
            messages=True,
            daily_summary=False,
            weekly_summary=True,
        )
        pref = await notification_pref_service.update(user_id, payload)
        assert pref.push_enabled is True
        assert pref.email_enabled is False
        assert pref.high_confidence_projects is True
        assert pref.new_opportunities is False
        assert pref.messages is True
        assert pref.daily_summary is False
        assert pref.weekly_summary is True
