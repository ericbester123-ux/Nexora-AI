"""
Unit tests for TechnologyService.
"""

import uuid

import pytest
from app.core.exceptions import NotFoundError
from app.models.technology import Technology
from app.schemas.technology import TechnologyCreate, TechnologyUpdate
from app.services.technology_service import TechnologyService


class FakeTechnologyRepository:
    def __init__(self):
        self._technologies: dict[uuid.UUID, Technology] = {}

    async def create(
        self, *, name: str, slug: str, description: str | None = None, category: str | None = None
    ) -> Technology:
        technology = Technology(
            id=uuid.uuid4(),
            name=name,
            slug=slug,
            description=description,
            category=category,
            is_active=True,
        )
        self._technologies[technology.id] = technology
        return technology

    async def get_by_id(self, technology_id: uuid.UUID) -> Technology | None:
        return self._technologies.get(technology_id)

    async def get_by_name(self, name: str) -> Technology | None:
        for tech in self._technologies.values():
            if tech.name == name:
                return tech
        return None

    async def get_by_slug(self, slug: str) -> Technology | None:
        for tech in self._technologies.values():
            if tech.slug == slug:
                return tech
        return None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Technology], int]:
        items = list(self._technologies.values())
        if search:
            items = [t for t in items if search.lower() in t.name.lower()]
        if category:
            items = [t for t in items if t.category == category]
        if is_active is not None:
            items = [t for t in items if t.is_active == is_active]
        total = len(items)
        items = items[skip : skip + limit]
        return items, total

    async def update(self, technology: Technology, **fields) -> Technology:
        for key, value in fields.items():
            setattr(technology, key, value)
        return technology

    async def delete(self, technology: Technology) -> None:
        self._technologies.pop(technology.id, None)


@pytest.fixture
def technology_service() -> TechnologyService:
    return TechnologyService(repository=FakeTechnologyRepository())


@pytest.fixture
async def existing_technology(technology_service: TechnologyService) -> Technology:
    technology = Technology(
        id=uuid.uuid4(),
        name="Python",
        slug="python",
        description="A programming language.",
        category="Language",
        is_active=True,
    )
    technology_service._repo._technologies[technology.id] = technology
    return technology


class TestCreate:
    async def test_create_technology(self, technology_service: TechnologyService):
        payload = TechnologyCreate(name="FastAPI", description="Web framework", category="Framework")
        result = await technology_service.create(payload)
        assert result.name == "FastAPI"
        assert result.slug is not None
        assert result.category == "Framework"
        assert result.is_active is True

    async def test_create_technology_generates_unique_slug(self, technology_service: TechnologyService, existing_technology: Technology):
        payload = TechnologyCreate(name="Python!")
        result = await technology_service.create(payload)
        assert result.name == "Python!"
        assert result.slug != "python"


class TestGetById:
    async def test_get_by_id_returns_technology(self, technology_service: TechnologyService, existing_technology: Technology):
        result = await technology_service.get_by_id(existing_technology.id)
        assert result.id == existing_technology.id
        assert result.name == existing_technology.name

    async def test_get_by_id_raises_not_found(self, technology_service: TechnologyService):
        with pytest.raises(NotFoundError):
            await technology_service.get_by_id(uuid.uuid4())


class TestGetBySlug:
    async def test_get_by_slug_returns_technology(self, technology_service: TechnologyService, existing_technology: Technology):
        result = await technology_service.get_by_slug(existing_technology.slug)
        assert result.id == existing_technology.id
        assert result.slug == existing_technology.slug

    async def test_get_by_slug_raises_not_found(self, technology_service: TechnologyService):
        with pytest.raises(NotFoundError):
            await technology_service.get_by_slug("nonexistent")


class TestGetAll:
    async def test_get_all_returns_paginated_results(self, technology_service: TechnologyService, existing_technology: Technology):
        items, total = await technology_service.get_all()
        assert total >= 1
        assert all(isinstance(item, Technology) for item in items)

    async def test_get_all_with_search_filter(self, technology_service: TechnologyService, existing_technology: Technology):
        items, total = await technology_service.get_all(search="python")
        assert total == 1
        assert items[0].name == "Python"

    async def test_get_all_with_category_filter(self, technology_service: TechnologyService, existing_technology: Technology):
        items, total = await technology_service.get_all(category="Language")
        assert total == 1
        assert items[0].category == "Language"

    async def test_get_all_with_is_active_filter(self, technology_service: TechnologyService, existing_technology: Technology):
        items, total = await technology_service.get_all(is_active=True)
        assert total >= 1

    async def test_get_all_with_pagination(self, technology_service: TechnologyService, existing_technology: Technology):
        items, total = await technology_service.get_all(skip=0, limit=1)
        assert len(items) <= 1
        assert total >= 1


class TestUpdate:
    async def test_update_technology(self, technology_service: TechnologyService, existing_technology: Technology):
        payload = TechnologyUpdate(name="Python 3")
        result = await technology_service.update(existing_technology.id, payload)
        assert result.name == "Python 3"

    async def test_update_technology_raises_not_found(self, technology_service: TechnologyService):
        payload = TechnologyUpdate(name="Ghost")
        with pytest.raises(NotFoundError):
            await technology_service.update(uuid.uuid4(), payload)


class TestDelete:
    async def test_delete_technology(self, technology_service: TechnologyService, existing_technology: Technology):
        await technology_service.delete(existing_technology.id)
        with pytest.raises(NotFoundError):
            await technology_service.get_by_id(existing_technology.id)

    async def test_delete_technology_raises_not_found(self, technology_service: TechnologyService):
        with pytest.raises(NotFoundError):
            await technology_service.delete(uuid.uuid4())
