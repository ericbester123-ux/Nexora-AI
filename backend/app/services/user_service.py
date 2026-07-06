"""
User profile application service.
"""

import uuid

from app.core.exceptions import NotFoundError
from app.schemas.user import UserProfileUpdate
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
