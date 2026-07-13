"""
Repository for ProjectCategory persistence operations.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project_category import ProjectCategory


class CategoryRepository:
    """Data access layer for the `ProjectCategory` entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, *, name: str, slug: str, description: str | None = None, icon: str | None = None) -> ProjectCategory:
        category = ProjectCategory(
            name=name,
            slug=slug,
            description=description,
            icon=icon,
        )
        self._session.add(category)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def get_by_id(self, category_id: uuid.UUID) -> Optional[ProjectCategory]:
        result = await self._session.execute(
            select(ProjectCategory).where(ProjectCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[ProjectCategory]:
        result = await self._session.execute(
            select(ProjectCategory).where(ProjectCategory.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 20, search: str | None = None, is_active: bool | None = None) -> tuple[list[ProjectCategory], int]:
        query = select(ProjectCategory)
        count_query = select(func.count(ProjectCategory.id))

        if search:
            pattern = f"%{search}%"
            query = query.where(ProjectCategory.name.ilike(pattern))
            count_query = count_query.where(ProjectCategory.name.ilike(pattern))
        if is_active is not None:
            query = query.where(ProjectCategory.is_active == is_active)
            count_query = count_query.where(ProjectCategory.is_active == is_active)

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar_one()

        query = query.order_by(ProjectCategory.name).offset(skip).limit(limit)
        result = await self._session.execute(query)
        categories = list(result.scalars().all())

        return categories, total_count

    async def update(self, category: ProjectCategory, **fields) -> ProjectCategory:
        for key, value in fields.items():
            setattr(category, key, value)
        await self._session.flush()
        await self._session.refresh(category)
        return category

    async def delete(self, category: ProjectCategory) -> None:
        await self._session.delete(category)
        await self._session.flush()
