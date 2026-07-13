"""
Category application service.
"""

import uuid

from app.core.exceptions import ConflictError, NotFoundError
from app.core.slug import slugify, unique_slug
from app.models.project_category import ProjectCategory
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Encapsulates business logic for managing project categories."""

    def __init__(self, repo: CategoryRepository):
        self._repo = repo

    async def create(self, payload: CategoryCreate) -> ProjectCategory:
        existing = await self._repo.get_by_slug(slugify(payload.name))
        if existing:
            raise ConflictError("A category with this name already exists.")
        slug = await self._generate_unique_slug(payload.name)
        return await self._repo.create(
            name=payload.name,
            slug=slug,
            description=payload.description,
            icon=payload.icon,
        )

    async def get_by_id(self, category_id: uuid.UUID) -> ProjectCategory:
        category = await self._repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    async def get_by_slug(self, slug: str) -> ProjectCategory:
        category = await self._repo.get_by_slug(slug)
        if category is None:
            raise NotFoundError("Category not found.")
        return category

    async def get_all(self, skip: int = 0, limit: int = 20, search: str | None = None, is_active: bool | None = None) -> tuple[list[ProjectCategory], int]:
        return await self._repo.get_all(skip=skip, limit=limit, search=search, is_active=is_active)

    async def update(self, category_id: uuid.UUID, payload: CategoryUpdate) -> ProjectCategory:
        category = await self.get_by_id(category_id)
        update_data = payload.model_dump(exclude_unset=True)
        if "name" in update_data:
            new_slug = slugify(update_data["name"])[:120]
            existing = await self._repo.get_by_slug(new_slug)
            if existing and existing.id != category_id:
                raise ConflictError("A category with this name already exists.")
            update_data["slug"] = new_slug
        return await self._repo.update(category, **update_data)

    async def delete(self, category_id: uuid.UUID) -> None:
        category = await self.get_by_id(category_id)
        await self._repo.delete(category)

    async def _generate_unique_slug(self, name: str) -> str:
        return await unique_slug(name, self._slug_exists)

    async def _slug_exists(self, slug: str) -> bool:
        existing = await self._repo.get_by_slug(slug)
        return existing is not None
