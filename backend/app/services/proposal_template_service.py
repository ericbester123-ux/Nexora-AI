"""
ProposalTemplate application service.
"""

import uuid
from typing import Optional

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.proposal_template import ProposalTemplate
from app.repositories.proposal_template_repository import ProposalTemplateRepository
from app.schemas.proposal_template import (
    ProposalTemplateCreate,
    ProposalTemplateUpdate,
)


class ProposalTemplateService:
    """Encapsulates business logic for managing proposal templates."""

    def __init__(self, repo: ProposalTemplateRepository):
        self._repo = repo

    async def create(self, user_id: uuid.UUID, payload: ProposalTemplateCreate) -> ProposalTemplate:
        return await self._repo.create(
            user_id=user_id,
            name=payload.name,
            cover_letter_template=payload.cover_letter_template,
            description=payload.description,
            category=payload.category,
            tags=payload.tags,
        )

    async def get_by_id(self, template_id: uuid.UUID, user_id: uuid.UUID | None = None) -> ProposalTemplate:
        template = await self._repo.get_by_id(template_id)
        if template is None:
            raise NotFoundError("Proposal template not found.")
        self._assert_ownership(template, user_id)
        return template

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[ProposalTemplate], int]:
        return await self._repo.get_by_user_id(
            user_id, skip=skip, limit=limit, search=search, category=category, is_active=is_active
        )

    async def update(
        self, template_id: uuid.UUID, payload: ProposalTemplateUpdate, user_id: uuid.UUID | None = None
    ) -> ProposalTemplate:
        template = await self.get_by_id(template_id, user_id=user_id)
        return await self._repo.update(template, **payload.model_dump(exclude_unset=True))

    async def delete(self, template_id: uuid.UUID, user_id: uuid.UUID | None = None) -> None:
        template = await self.get_by_id(template_id, user_id=user_id)
        await self._repo.delete(template)

    @staticmethod
    def _assert_ownership(template: ProposalTemplate, user_id: uuid.UUID | None) -> None:
        if user_id is not None and template.user_id != user_id:
            raise AuthorizationError("You do not have permission to access this proposal template.")
