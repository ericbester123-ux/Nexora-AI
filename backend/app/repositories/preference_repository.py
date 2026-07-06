"""
Repository for user preference persistence operations.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_preference import AIPreference
from app.models.notification_preference import NotificationPreference
from app.models.user_preference import UserPreference


class UserPreferenceRepository:
    """Data access layer for UserPreference entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> UserPreference | None:
        result = await self._session.execute(
            select(UserPreference).where(UserPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **fields) -> UserPreference:
        existing = await self.get_by_user_id(user_id)
        if existing is not None:
            for key, value in fields.items():
                if value is not None:
                    setattr(existing, key, value)
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        pref = UserPreference(user_id=user_id, **{k: v for k, v in fields.items() if v is not None})
        self._session.add(pref)
        await self._session.flush()
        await self._session.refresh(pref)
        return pref


class AIPreferenceRepository:
    """Data access layer for AIPreference entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> AIPreference | None:
        result = await self._session.execute(
            select(AIPreference).where(AIPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **fields) -> AIPreference:
        existing = await self.get_by_user_id(user_id)
        if existing is not None:
            for key, value in fields.items():
                if value is not None:
                    setattr(existing, key, value)
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        pref = AIPreference(user_id=user_id, **{k: v for k, v in fields.items() if v is not None})
        self._session.add(pref)
        await self._session.flush()
        await self._session.refresh(pref)
        return pref


class NotificationPreferenceRepository:
    """Data access layer for NotificationPreference entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> NotificationPreference | None:
        result = await self._session.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **fields) -> NotificationPreference:
        existing = await self.get_by_user_id(user_id)
        if existing is not None:
            for key, value in fields.items():
                if value is not None:
                    setattr(existing, key, value)
            await self._session.flush()
            await self._session.refresh(existing)
            return existing

        pref = NotificationPreference(
            user_id=user_id, **{k: v for k, v in fields.items() if v is not None}
        )
        self._session.add(pref)
        await self._session.flush()
        await self._session.refresh(pref)
        return pref
