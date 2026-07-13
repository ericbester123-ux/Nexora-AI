"""
User profile application service.
"""

import uuid
from datetime import datetime, timezone

from app.core.exceptions import NotFoundError
from app.schemas.user import UserProfileUpdate, UserSubscriptionUpdate
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    """Encapsulates business logic for reading and updating user profiles."""

    def __init__(self, user_repository: UserRepository):
        self._users = user_repository

    async def get_profile(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def update_profile(self, user_id: uuid.UUID, payload: UserProfileUpdate) -> User:
        user = await self.get_profile(user_id)
        return await self._users.update(user, **payload.model_dump(exclude_unset=True))

    async def update_freelancer_profile(
        self,
        user_id: uuid.UUID,
        *,
        freelancer_user_id: str | None = None,
        freelancer_oauth_token: str | None = None,
        freelancer_refresh_token: str | None = None,
        freelancer_token_expires_at: datetime | None = None,
        freelancer_connected_at: datetime | None = None,
    ) -> User:
        """Update Freelancer-specific profile fields."""
        user = await self.get_profile(user_id)
        update_data = {}
        if freelancer_user_id is not None:
            update_data["freelancer_user_id"] = freelancer_user_id
        if freelancer_oauth_token is not None:
            update_data["freelancer_oauth_token"] = freelancer_oauth_token
        if freelancer_refresh_token is not None:
            update_data["freelancer_refresh_token"] = freelancer_refresh_token
        if freelancer_token_expires_at is not None:
            update_data["freelancer_token_expires_at"] = freelancer_token_expires_at
        if freelancer_connected_at is not None:
            update_data["freelancer_connected_at"] = freelancer_connected_at
        if update_data:
            return await self._users.update(user, **update_data)
        return user

    async def update_subscription(
        self,
        user_id: uuid.UUID,
        payload: UserSubscriptionUpdate,
    ) -> User:
        user = await self.get_profile(user_id)
        update_data = payload.model_dump(exclude_unset=True)
        return await self._users.update(user, **update_data)
