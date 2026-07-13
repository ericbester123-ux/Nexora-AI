"""
Repository for Client persistence operations.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client


class ClientRepository:
    """Data access layer for the `Client` entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, user_id: uuid.UUID, name: str, **fields) -> Client:
        client = Client(user_id=user_id, name=name, **fields)
        self._session.add(client)
        await self._session.flush()
        await self._session.refresh(client)
        return client

    async def get_by_id(self, client_id: uuid.UUID) -> Optional[Client]:
        result = await self._session.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Client], int]:
        query = select(Client).where(Client.user_id == user_id)
        count_query = (
            select(func.count()).select_from(Client).where(Client.user_id == user_id)
        )

        if search:
            search_filter = Client.name.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        if is_active is not None:
            query = query.where(Client.is_active == is_active)
            count_query = count_query.where(Client.is_active == is_active)

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        result = await self._session.execute(
            query.order_by(Client.created_at.desc()).offset(skip).limit(limit)
        )
        clients = list(result.scalars().all())

        return clients, total_count

    async def update(self, client: Client, **fields) -> Client:
        for key, value in fields.items():
            setattr(client, key, value)
        await self._session.flush()
        await self._session.refresh(client)
        return client

    async def delete(self, client: Client) -> None:
        await self._session.delete(client)
        await self._session.flush()
