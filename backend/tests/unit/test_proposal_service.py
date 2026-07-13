"""
Unit tests for ProposalService.
"""

import uuid
from decimal import Decimal

import pytest
from app.core.exceptions import NotFoundError
from app.models.proposal import Proposal
from app.schemas.proposal import ProposalCreate, ProposalUpdate
from app.services.proposal_service import ProposalService


class FakeProposalRepository:
    def __init__(self):
        self._proposals: dict[uuid.UUID, Proposal] = {}

    async def create(
        self, user_id: uuid.UUID, project_id: uuid.UUID, **fields
    ) -> Proposal:
        fields.setdefault("status", "draft")
        fields.setdefault("currency", "USD")
        fields.setdefault("ai_generated", False)
        fields.setdefault("is_auto_submitted", False)
        fields.setdefault("requires_human_approval", True)
        fields.setdefault("client_interview_request", False)
        proposal = Proposal(
            id=uuid.uuid4(),
            user_id=user_id,
            project_id=project_id,
            **fields,
        )
        self._proposals[proposal.id] = proposal
        return proposal

    async def get_by_id(self, proposal_id: uuid.UUID) -> Proposal | None:
        return self._proposals.get(proposal_id)

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        status: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> tuple[list[Proposal], int]:
        items = list(self._proposals.values())
        items = [p for p in items if p.user_id == user_id]
        if status:
            items = [p for p in items if p.status == status]
        if project_id:
            items = [p for p in items if p.project_id == project_id]
        if search:
            items = [p for p in items if p.cover_letter and search.lower() in p.cover_letter.lower()]
        items.sort(key=lambda p: p.created_at if p.created_at else None, reverse=True)
        total = len(items)
        items = items[skip : skip + limit]
        return items, total

    async def update(self, proposal: Proposal, **fields) -> Proposal:
        for key, value in fields.items():
            setattr(proposal, key, value)
        return proposal

    async def delete(self, proposal: Proposal) -> None:
        self._proposals.pop(proposal.id, None)


@pytest.fixture
def proposal_service() -> ProposalService:
    return ProposalService(repository=FakeProposalRepository())


@pytest.fixture
async def existing_proposal(proposal_service: ProposalService) -> Proposal:
    proposal = Proposal(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        status="draft",
        cover_letter="I am interested in this project.",
        currency="USD",
    )
    proposal_service._repo._proposals[proposal.id] = proposal
    return proposal


class TestCreate:
    async def test_create_proposal(self, proposal_service: ProposalService):
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        payload = ProposalCreate(
            project_id=project_id,
            cover_letter="I can do this job.",
            bid_amount=Decimal("500.00"),
        )
        result = await proposal_service.create(user_id=user_id, payload=payload)
        assert result.user_id == user_id
        assert result.project_id == project_id
        assert result.cover_letter == "I can do this job."
        assert result.bid_amount == Decimal("500.00")
        assert result.status == "draft"
        assert result.currency == "USD"
        assert result.requires_human_approval is True
        assert result.ai_generated is False
        assert result.client_interview_request is False

    async def test_create_proposal_with_template(self, proposal_service: ProposalService):
        user_id = uuid.uuid4()
        project_id = uuid.uuid4()
        template_id = uuid.uuid4()
        payload = ProposalCreate(
            project_id=project_id,
            template_id=template_id,
            cover_letter="Using a template.",
        )
        result = await proposal_service.create(user_id=user_id, payload=payload)
        assert result.template_id == template_id


class TestGetById:
    async def test_get_by_id_returns_proposal(self, proposal_service: ProposalService, existing_proposal: Proposal):
        result = await proposal_service.get_by_id(existing_proposal.id)
        assert result.id == existing_proposal.id
        assert result.cover_letter == existing_proposal.cover_letter

    async def test_get_by_id_raises_not_found(self, proposal_service: ProposalService):
        with pytest.raises(NotFoundError):
            await proposal_service.get_by_id(uuid.uuid4())


class TestGetAll:
    async def test_get_all_returns_paginated_results(self, proposal_service: ProposalService, existing_proposal: Proposal):
        items, total = await proposal_service.get_all(user_id=existing_proposal.user_id)
        assert total >= 1
        assert all(isinstance(item, Proposal) for item in items)

    async def test_get_all_filters_by_user_id(self, proposal_service: ProposalService, existing_proposal: Proposal):
        items, total = await proposal_service.get_all(user_id=uuid.uuid4())
        assert total == 0

    async def test_get_all_with_status_filter(self, proposal_service: ProposalService, existing_proposal: Proposal):
        items, total = await proposal_service.get_all(user_id=existing_proposal.user_id, status="draft")
        assert total == 1

    async def test_get_all_with_project_id_filter(self, proposal_service: ProposalService, existing_proposal: Proposal):
        items, total = await proposal_service.get_all(user_id=existing_proposal.user_id, project_id=existing_proposal.project_id)
        assert total == 1

    async def test_get_all_with_pagination(self, proposal_service: ProposalService, existing_proposal: Proposal):
        items, total = await proposal_service.get_all(user_id=existing_proposal.user_id, skip=0, limit=1)
        assert len(items) <= 1
        assert total >= 1


class TestUpdate:
    async def test_update_proposal(self, proposal_service: ProposalService, existing_proposal: Proposal):
        payload = ProposalUpdate(cover_letter="Updated cover letter.", status="submitted")
        result = await proposal_service.update(existing_proposal.id, payload)
        assert result.cover_letter == "Updated cover letter."
        assert result.status == "submitted"

    async def test_update_proposal_raises_not_found(self, proposal_service: ProposalService):
        payload = ProposalUpdate(cover_letter="Ghost")
        with pytest.raises(NotFoundError):
            await proposal_service.update(uuid.uuid4(), payload)


class TestDelete:
    async def test_delete_proposal(self, proposal_service: ProposalService, existing_proposal: Proposal):
        await proposal_service.delete(existing_proposal.id)
        with pytest.raises(NotFoundError):
            await proposal_service.get_by_id(existing_proposal.id)

    async def test_delete_proposal_raises_not_found(self, proposal_service: ProposalService):
        with pytest.raises(NotFoundError):
            await proposal_service.delete(uuid.uuid4())
