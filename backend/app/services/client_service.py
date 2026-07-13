"""
Client application service.
"""

import uuid

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.client import Client
from app.repositories.client_repository import ClientRepository
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    """Encapsulates business logic for client CRUD operations."""

    def __init__(self, repo: ClientRepository):
        self._repo = repo

    async def create(self, user_id: uuid.UUID, payload: ClientCreate) -> Client:
        return await self._repo.create(
            user_id=user_id,
            name=payload.name,
            **payload.model_dump(exclude={"name"}, exclude_none=True),
        )

    async def get_by_id(self, client_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Client:
        client = await self._repo.get_by_id(client_id)
        if client is None:
            raise NotFoundError("Client not found.")
        self._assert_ownership(client, user_id)
        return client

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Client], int]:
        return await self._repo.get_by_user_id(
            user_id, skip=skip, limit=limit, search=search, is_active=is_active
        )

    async def update(self, client_id: uuid.UUID, payload: ClientUpdate, user_id: uuid.UUID | None = None) -> Client:
        client = await self.get_by_id(client_id, user_id=user_id)
        return await self._repo.update(client, **payload.model_dump(exclude_unset=True))

    async def delete(self, client_id: uuid.UUID, user_id: uuid.UUID | None = None) -> None:
        client = await self.get_by_id(client_id, user_id=user_id)
        await self._repo.delete(client)

    @staticmethod
    def _assert_ownership(client: Client, user_id: uuid.UUID | None) -> None:
        if user_id is not None and client.user_id != user_id:
            raise AuthorizationError("You do not have permission to access this client.")
