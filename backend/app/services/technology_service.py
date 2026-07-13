"""
Technology application service.
"""

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.slug import unique_slug
from app.models.technology import Technology
from app.repositories.technology_repository import TechnologyRepository
from app.schemas.technology import TechnologyCreate, TechnologyUpdate


class TechnologyService:
    """Encapsulates business logic for managing technologies."""

    def __init__(self, repository: TechnologyRepository):
        self._repo = repository

    async def create(self, payload: TechnologyCreate) -> Technology:
        existing_name = await self._repo.get_by_name(payload.name)
        if existing_name:
            raise ConflictError(f"A technology with name '{payload.name}' already exists.")

        async def slug_exists(slug: str) -> bool:
            found = await self._repo.get_by_slug(slug)
            return found is not None

        slug = await unique_slug(payload.name, slug_exists, max_length=120)
        return await self._repo.create(
            name=payload.name,
            slug=slug,
            description=payload.description,
            category=payload.category,
        )

    async def get_by_id(self, technology_id: uuid.UUID) -> Technology:
        technology = await self._repo.get_by_id(technology_id)
        if technology is None:
            raise NotFoundError("Technology not found.")
        return technology

    async def get_by_slug(self, slug: str) -> Technology:
        technology = await self._repo.get_by_slug(slug)
        if technology is None:
            raise NotFoundError("Technology not found.")
        return technology

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Technology], int]:
        return await self._repo.get_all(
            skip=skip,
            limit=limit,
            search=search,
            category=category,
            is_active=is_active,
        )

    async def update(self, technology_id: uuid.UUID, payload: TechnologyUpdate) -> Technology:
        technology = await self.get_by_id(technology_id)
        return await self._repo.update(technology, **payload.model_dump(exclude_unset=True))

    async def delete(self, technology_id: uuid.UUID) -> None:
        technology = await self.get_by_id(technology_id)
        await self._repo.delete(technology)
