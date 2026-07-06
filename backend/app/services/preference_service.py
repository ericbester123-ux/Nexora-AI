"""
Preference application services.
"""

import uuid

from app.repositories.preference_repository import (
    AIPreferenceRepository,
    NotificationPreferenceRepository,
    UserPreferenceRepository,
)
from app.schemas.preferences import (
    AIPreferencesUpdate,
    NotificationPreferencesUpdate,
    UserPreferencesUpdate,
)


class UserPreferenceService:
    """Business logic for reading and updating user project-matching preferences."""

    def __init__(self, preference_repository: UserPreferenceRepository):
        self._repo = preference_repository

    async def get(self, user_id: uuid.UUID):
        pref = await self._repo.get_by_user_id(user_id)
        if pref is None:
            pref = await self._repo.upsert(user_id)
        return pref

    async def update(self, user_id: uuid.UUID, payload: UserPreferencesUpdate):
        return await self._repo.upsert(user_id, **payload.model_dump(exclude_none=True))


class AIPreferenceService:
    """Business logic for reading and updating AI settings."""

    def __init__(self, ai_preference_repository: AIPreferenceRepository):
        self._repo = ai_preference_repository

    async def get(self, user_id: uuid.UUID):
        pref = await self._repo.get_by_user_id(user_id)
        if pref is None:
            pref = await self._repo.upsert(user_id)
        return pref

    async def update(self, user_id: uuid.UUID, payload: AIPreferencesUpdate):
        return await self._repo.upsert(user_id, **payload.model_dump(exclude_none=True))


class NotificationPreferenceService:
    """Business logic for reading and updating notification preferences."""

    def __init__(self, notification_preference_repository: NotificationPreferenceRepository):
        self._repo = notification_preference_repository

    async def get(self, user_id: uuid.UUID):
        pref = await self._repo.get_by_user_id(user_id)
        if pref is None:
            pref = await self._repo.upsert(user_id)
        return pref

    async def update(self, user_id: uuid.UUID, payload: NotificationPreferencesUpdate):
        return await self._repo.upsert(user_id, **payload.model_dump(exclude_none=True))
