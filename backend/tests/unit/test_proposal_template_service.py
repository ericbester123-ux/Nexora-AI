"""
Unit tests for ProposalTemplateService.
"""

import uuid

import pytest
from app.core.exceptions import NotFoundError
from app.models.proposal_template import ProposalTemplate
from app.schemas.proposal_template import (
    ProposalTemplateCreate,
    ProposalTemplateUpdate,
)
from app.services.proposal_template_service import ProposalTemplateService


class FakeProposalTemplateRepository:
    def __init__(self):
        self._templates: dict[uuid.UUID, ProposalTemplate] = {}

    async def create(self, *, user_id, name, cover_letter_template, **fields):
        fields.setdefault("is_default", False)
        fields.setdefault("is_active", True)
        template = ProposalTemplate(
            id=uuid.uuid4(),
            user_id=user_id,
            name=name,
            cover_letter_template=cover_letter_template,
            **fields,
        )
        self._templates[template.id] = template
        return template

    async def get_by_id(self, template_id):
        return self._templates.get(template_id)

    async def get_by_user_id(self, user_id, skip=0, limit=20, search=None, category=None, is_active=None):
        items = [t for t in self._templates.values() if t.user_id == user_id]
        if search:
            items = [t for t in items if search.lower() in t.name.lower()]
        if category is not None:
            items = [t for t in items if t.category == category]
        if is_active is not None:
            items = [t for t in items if t.is_active == is_active]
        total = len(items)
        items = items[skip:skip + limit]
        return items, total

    async def update(self, template, **fields):
        for key, value in fields.items():
            setattr(template, key, value)
        return template

    async def delete(self, template):
        self._templates.pop(template.id, None)


@pytest.fixture
def service() -> ProposalTemplateService:
    return ProposalTemplateService(FakeProposalTemplateRepository())


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


class TestCreate:
    async def test_create_returns_template_response(self, service: ProposalTemplateService, user_id: uuid.UUID):
        payload = ProposalTemplateCreate(
            name="Standard Proposal",
            cover_letter_template="Dear {{client_name}}, ...",
            description="A standard proposal template",
            category="web-dev",
            tags=["web", "react"],
        )
        result = await service.create(user_id, payload)
        assert result.name == "Standard Proposal"
        assert result.cover_letter_template == "Dear {{client_name}}, ..."
        assert result.description == "A standard proposal template"
        assert result.category == "web-dev"
        assert result.tags == ["web", "react"]
        assert result.user_id == user_id
        assert result.is_default is False
        assert result.is_active is True

    async def test_create_minimal_fields(self, service: ProposalTemplateService, user_id: uuid.UUID):
        payload = ProposalTemplateCreate(
            name="Minimal",
            cover_letter_template="Hello",
        )
        result = await service.create(user_id, payload)
        assert result.name == "Minimal"
        assert result.description is None


class TestGetById:
    async def test_get_by_id_returns_template(self, service: ProposalTemplateService, user_id: uuid.UUID):
        created = await service.create(
            user_id,
            ProposalTemplateCreate(name="Test", cover_letter_template="Body"),
        )
        result = await service.get_by_id(created.id)
        assert result.id == created.id
        assert result.name == "Test"

    async def test_get_by_id_raises_not_found(self, service: ProposalTemplateService):
        with pytest.raises(NotFoundError):
            await service.get_by_id(uuid.uuid4())


class TestGetByUserId:
    async def test_returns_templates_for_user(self, service: ProposalTemplateService, user_id: uuid.UUID):
        await service.create(user_id, ProposalTemplateCreate(name="A", cover_letter_template="X"))
        await service.create(user_id, ProposalTemplateCreate(name="B", cover_letter_template="Y"))
        items, total = await service.get_by_user_id(user_id)
        assert total == 2
        assert len(items) == 2

    async def test_pagination(self, service: ProposalTemplateService, user_id: uuid.UUID):
        for i in range(5):
            await service.create(user_id, ProposalTemplateCreate(name=f"T{i}", cover_letter_template="X"))
        items, total = await service.get_by_user_id(user_id, skip=0, limit=2)
        assert total == 5
        assert len(items) == 2

    async def test_search_filter(self, service: ProposalTemplateService, user_id: uuid.UUID):
        await service.create(user_id, ProposalTemplateCreate(name="Python Dev", cover_letter_template="X"))
        await service.create(user_id, ProposalTemplateCreate(name="React Dev", cover_letter_template="Y"))
        items, total = await service.get_by_user_id(user_id, search="python")
        assert total == 1
        assert items[0].name == "Python Dev"

    async def test_category_filter(self, service: ProposalTemplateService, user_id: uuid.UUID):
        await service.create(
            user_id, ProposalTemplateCreate(name="Web", cover_letter_template="X", category="web")
        )
        await service.create(
            user_id, ProposalTemplateCreate(name="Mobile", cover_letter_template="Y", category="mobile")
        )
        items, total = await service.get_by_user_id(user_id, category="web")
        assert total == 1
        assert items[0].name == "Web"

    async def test_is_active_filter(self, service: ProposalTemplateService, user_id: uuid.UUID):
        t1 = await service.create(user_id, ProposalTemplateCreate(name="Active", cover_letter_template="X"))
        t2 = await service.create(user_id, ProposalTemplateCreate(name="Inactive", cover_letter_template="Y"))
        await service.update(t1.id, ProposalTemplateUpdate(is_active=False))
        items, total = await service.get_by_user_id(user_id, is_active=True)
        assert total == 1
        assert items[0].name == "Inactive"


class TestUpdate:
    async def test_update_updates_fields(self, service: ProposalTemplateService, user_id: uuid.UUID):
        created = await service.create(
            user_id,
            ProposalTemplateCreate(name="Original", cover_letter_template="Original body"),
        )
        result = await service.update(
            created.id,
            ProposalTemplateUpdate(name="Updated", cover_letter_template="Updated body"),
        )
        assert result.name == "Updated"
        assert result.cover_letter_template == "Updated body"

    async def test_update_partial(self, service: ProposalTemplateService, user_id: uuid.UUID):
        created = await service.create(
            user_id,
            ProposalTemplateCreate(
                name="Original", cover_letter_template="Body", description="Old desc"
            ),
        )
        result = await service.update(created.id, ProposalTemplateUpdate(description="New desc"))
        assert result.name == "Original"
        assert result.description == "New desc"

    async def test_update_raises_not_found(self, service: ProposalTemplateService):
        with pytest.raises(NotFoundError):
            await service.update(uuid.uuid4(), ProposalTemplateUpdate(name="X"))


class TestDelete:
    async def test_delete_removes_template(self, service: ProposalTemplateService, user_id: uuid.UUID):
        created = await service.create(
            user_id,
            ProposalTemplateCreate(name="ToDelete", cover_letter_template="Body"),
        )
        await service.delete(created.id)
        with pytest.raises(NotFoundError):
            await service.get_by_id(created.id)

    async def test_delete_raises_not_found(self, service: ProposalTemplateService):
        with pytest.raises(NotFoundError):
            await service.delete(uuid.uuid4())
