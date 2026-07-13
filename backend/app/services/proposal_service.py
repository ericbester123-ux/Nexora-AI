"""
Proposal application service.
"""

import uuid

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.proposal import Proposal
from app.repositories.proposal_repository import ProposalRepository
from app.schemas.proposal import ProposalCreate, ProposalUpdate


class ProposalService:
    """Encapsulates business logic for managing proposals."""

    def __init__(self, repository: ProposalRepository):
        self._repo = repository

    async def create(self, user_id: uuid.UUID, payload: ProposalCreate) -> Proposal:
        return await self._repo.create(
            user_id=user_id,
            project_id=payload.project_id,
            **payload.model_dump(exclude={"project_id", "template_id"}, exclude_none=True),
            template_id=payload.template_id,
        )

    async def get_by_id(self, proposal_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Proposal:
        proposal = await self._repo.get_by_id(proposal_id)
        if proposal is None:
            raise NotFoundError("Proposal not found.")
        self._assert_ownership(proposal, user_id)
        return proposal

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        status: str | None = None,
        project_id: uuid.UUID | None = None,
    ) -> tuple[list[Proposal], int]:
        return await self._repo.get_all(
            user_id=user_id,
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            project_id=project_id,
        )

    async def update(self, proposal_id: uuid.UUID, payload: ProposalUpdate, user_id: uuid.UUID | None = None) -> Proposal:
        proposal = await self.get_by_id(proposal_id, user_id=user_id)
        return await self._repo.update(proposal, **payload.model_dump(exclude_unset=True))

    async def delete(self, proposal_id: uuid.UUID, user_id: uuid.UUID | None = None) -> None:
        proposal = await self.get_by_id(proposal_id, user_id=user_id)
        await self._repo.delete(proposal)

    @staticmethod
    def _assert_ownership(proposal: Proposal, user_id: uuid.UUID | None) -> None:
        if user_id is not None and proposal.user_id != user_id:
            raise AuthorizationError("You do not have permission to access this proposal.")
