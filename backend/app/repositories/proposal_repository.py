"""
Repository for Proposal persistence operations.
"""

import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposal import Proposal


class ProposalRepository:
    """Data access layer for the `Proposal` entity."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self, user_id: uuid.UUID, project_id: uuid.UUID, **fields
    ) -> Proposal:
        proposal = Proposal(user_id=user_id, project_id=project_id, **fields)
        self._session.add(proposal)
        await self._session.flush()
        await self._session.refresh(proposal)
        return proposal

    async def get_by_id(self, proposal_id: uuid.UUID) -> Optional[Proposal]:
        result = await self._session.execute(
            select(Proposal).where(Proposal.id == proposal_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[Proposal], int]:
        query = select(Proposal)
        count_query = select(func.count(Proposal.id))

        base_conditions = [Proposal.user_id == user_id]
        if status:
            base_conditions.append(Proposal.status == status)
        if project_id:
            base_conditions.append(Proposal.project_id == project_id)

        query = query.where(*base_conditions)
        count_query = count_query.where(*base_conditions)

        if search:
            pattern = f"%{search}%"
            query = query.where(Proposal.cover_letter.ilike(pattern))
            count_query = count_query.where(Proposal.cover_letter.ilike(pattern))

        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0

        query = query.order_by(Proposal.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, proposal: Proposal, **fields) -> Proposal:
        for key, value in fields.items():
            setattr(proposal, key, value)
        await self._session.flush()
        await self._session.refresh(proposal)
        return proposal

    async def delete(self, proposal: Proposal) -> None:
        await self._session.delete(proposal)
        await self._session.flush()
