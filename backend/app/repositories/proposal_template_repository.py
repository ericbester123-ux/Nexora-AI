"""
Repository for ProposalTemplate persistence operations.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposal_template import ProposalTemplate


class ProposalTemplateRepository:
    """Data access layer for the `ProposalTemplate` entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        name: str,
        cover_letter_template: str,
        **fields,
    ) -> ProposalTemplate:
        template = ProposalTemplate(
            user_id=user_id,
            name=name,
            cover_letter_template=cover_letter_template,
            **fields,
        )
        self._session.add(template)
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def get_by_id(self, template_id: uuid.UUID) -> Optional[ProposalTemplate]:
        result = await self._session.execute(
            select(ProposalTemplate).where(ProposalTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[ProposalTemplate], int]:
        query = select(ProposalTemplate).where(ProposalTemplate.user_id == user_id)
        count_query = select(func.count()).select_from(ProposalTemplate).where(
            ProposalTemplate.user_id == user_id
        )

        if search:
            pattern = f"%{search}%"
            query = query.where(ProposalTemplate.name.ilike(pattern))
            count_query = count_query.where(ProposalTemplate.name.ilike(pattern))

        if category is not None:
            query = query.where(ProposalTemplate.category == category)
            count_query = count_query.where(ProposalTemplate.category == category)

        if is_active is not None:
            query = query.where(ProposalTemplate.is_active == is_active)
            count_query = count_query.where(ProposalTemplate.is_active == is_active)

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.order_by(ProposalTemplate.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        templates = list(result.scalars().all())

        return templates, total_count

    async def update(self, template: ProposalTemplate, **fields) -> ProposalTemplate:
        for key, value in fields.items():
            setattr(template, key, value)
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def delete(self, template: ProposalTemplate) -> None:
        await self._session.delete(template)
        await self._session.flush()
