"""
Unit tests for CategoryService.
"""

import uuid

import pytest
from app.core.exceptions import ConflictError, NotFoundError
from app.models.project_category import ProjectCategory
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services.category_service import CategoryService


class FakeCategoryRepository:
    def __init__(self):
        self._categories: dict[uuid.UUID, ProjectCategory] = {}

    async def create(self, *, name: str, slug: str, description: str | None = None, icon: str | None = None) -> ProjectCategory:
        category = ProjectCategory(
            id=uuid.uuid4(),
            name=name,
            slug=slug,
            description=description,
            icon=icon,
            is_active=True,
        )
        self._categories[category.id] = category
        return category

    async def get_by_id(self, category_id: uuid.UUID) -> ProjectCategory | None:
        return self._categories.get(category_id)

    async def get_by_slug(self, slug: str) -> ProjectCategory | None:
        for category in self._categories.values():
            if category.slug == slug:
                return category
        return None

    async def get_all(self, skip: int = 0, limit: int = 20, search: str | None = None, is_active: bool | None = None) -> tuple[list[ProjectCategory], int]:
        items = list(self._categories.values())
        if search:
            items = [c for c in items if search.lower() in c.name.lower()]
        if is_active is not None:
            items = [c for c in items if c.is_active == is_active]
        total = len(items)
        items = items[skip:skip + limit]
        return items, total

    async def update(self, category: ProjectCategory, **fields) -> ProjectCategory:
        for key, value in fields.items():
            setattr(category, key, value)
        return category

    async def delete(self, category: ProjectCategory) -> None:
        self._categories.pop(category.id, None)


@pytest.fixture
def category_service() -> CategoryService:
    return CategoryService(repo=FakeCategoryRepository())


@pytest.fixture
async def existing_category(category_service: CategoryService) -> ProjectCategory:
    cat = ProjectCategory(
        id=uuid.uuid4(),
        name="Web Development",
        slug="web-development",
        description="Build websites and web apps",
        icon="globe",
        is_active=True,
    )
    category_service._repo._categories[cat.id] = cat
    return cat


class TestCreate:
    async def test_create_returns_category(self, category_service: CategoryService):
        payload = CategoryCreate(name="Data Science", description="Work with data", icon="chart")
        result = await category_service.create(payload)
        assert result.name == "Data Science"
        assert result.description == "Work with data"
        assert result.icon == "chart"
        assert result.slug is not None
        assert result.is_active is True

    async def test_create_raises_conflict_for_duplicate_name(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryCreate(name="Web Development")
        with pytest.raises(ConflictError):
            await category_service.create(payload)


class TestGetById:
    async def test_get_by_id_returns_category(self, category_service: CategoryService, existing_category: ProjectCategory):
        result = await category_service.get_by_id(existing_category.id)
        assert result.id == existing_category.id
        assert result.name == existing_category.name

    async def test_get_by_id_raises_not_found_for_missing(self, category_service: CategoryService):
        with pytest.raises(NotFoundError):
            await category_service.get_by_id(uuid.uuid4())


class TestGetBySlug:
    async def test_get_by_slug_returns_category(self, category_service: CategoryService, existing_category: ProjectCategory):
        result = await category_service.get_by_slug(existing_category.slug)
        assert result.id == existing_category.id

    async def test_get_by_slug_raises_not_found_for_missing(self, category_service: CategoryService):
        with pytest.raises(NotFoundError):
            await category_service.get_by_slug("non-existent-slug")


class TestGetAll:
    async def test_get_all_returns_all(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryCreate(name="Data Science")
        await category_service.create(payload)
        items, total = await category_service.get_all()
        assert total == 2
        assert len(items) == 2

    async def test_get_all_pagination(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryCreate(name="Data Science")
        await category_service.create(payload)
        payload2 = CategoryCreate(name="DevOps")
        await category_service.create(payload2)

        items, total = await category_service.get_all(skip=0, limit=2)
        assert total == 3
        assert len(items) == 2

        items, total = await category_service.get_all(skip=2, limit=2)
        assert total == 3
        assert len(items) == 1

    async def test_get_all_search(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryCreate(name="Data Science")
        await category_service.create(payload)

        items, total = await category_service.get_all(search="data")
        assert total == 1
        assert items[0].name == "Data Science"

    async def test_get_all_filter_active(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryUpdate(is_active=False)
        await category_service.update(existing_category.id, payload)

        items, total = await category_service.get_all(is_active=True)
        assert total == 0

        items, total = await category_service.get_all(is_active=False)
        assert total == 1


class TestUpdate:
    async def test_update_updates_fields(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryUpdate(name="Web Dev Updated", description="Updated description")
        result = await category_service.update(existing_category.id, payload)
        assert result.name == "Web Dev Updated"
        assert result.description == "Updated description"

    async def test_update_partial_update(self, category_service: CategoryService, existing_category: ProjectCategory):
        payload = CategoryUpdate(description="Only description changed")
        result = await category_service.update(existing_category.id, payload)
        assert result.description == "Only description changed"
        assert result.name == existing_category.name

    async def test_update_raises_not_found_for_missing(self, category_service: CategoryService):
        payload = CategoryUpdate(name="Ghost")
        with pytest.raises(NotFoundError):
            await category_service.update(uuid.uuid4(), payload)


class TestDelete:
    async def test_delete_removes_category(self, category_service: CategoryService, existing_category: ProjectCategory):
        await category_service.delete(existing_category.id)
        with pytest.raises(NotFoundError):
            await category_service.get_by_id(existing_category.id)

    async def test_delete_raises_not_found_for_missing(self, category_service: CategoryService):
        with pytest.raises(NotFoundError):
            await category_service.delete(uuid.uuid4())
