"""
Repository for Technology persistence operations.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.technology import Technology


class TechnologyRepository:
    """Data access layer for the `Technology` entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, *, name: str, slug: str, description: Optional[str] = None, category: Optional[str] = None
    ) -> Technology:
        technology = Technology(
            name=name,
            slug=slug,
            description=description,
            category=category,
        )
        self._session.add(technology)
        await self._session.flush()
        await self._session.refresh(technology)
        return technology

    async def get_by_id(self, technology_id: uuid.UUID) -> Optional[Technology]:
        result = await self._session.execute(
            select(Technology).where(Technology.id == technology_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Technology]:
        result = await self._session.execute(
            select(Technology).where(Technology.name == name)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Technology]:
        result = await self._session.execute(
            select(Technology).where(Technology.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[Technology], int]:
        query = select(Technology)
        count_query = select(func.count(Technology.id))

        if search:
            pattern = f"%{search}%"
            query = query.where(Technology.name.ilike(pattern))
            count_query = count_query.where(Technology.name.ilike(pattern))
        if category:
            query = query.where(Technology.category == category)
            count_query = count_query.where(Technology.category == category)
        if is_active is not None:
            query = query.where(Technology.is_active == is_active)
            count_query = count_query.where(Technology.is_active == is_active)

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, technology: Technology, **fields) -> Technology:
        for key, value in fields.items():
            setattr(technology, key, value)
        await self._session.flush()
        await self._session.refresh(technology)
        return technology

    async def delete(self, technology: Technology) -> None:
        await self._session.delete(technology)
        await self._session.flush()
