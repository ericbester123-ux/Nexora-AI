import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposal_version import ProposalVersion


class ProposalVersionRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, version_id: uuid.UUID) -> Optional[ProposalVersion]:
        result = await self._session.execute(
            select(ProposalVersion).where(ProposalVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_and_proposal_id(
        self, version_id: uuid.UUID, proposal_id: uuid.UUID
    ) -> Optional[ProposalVersion]:
        result = await self._session.execute(
            select(ProposalVersion).where(
                ProposalVersion.id == version_id,
                ProposalVersion.proposal_id == proposal_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_proposal_id(
        self, proposal_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ProposalVersion], int]:
        query = select(ProposalVersion).where(ProposalVersion.proposal_id == proposal_id)
        count_query = select(func.count(ProposalVersion.id)).where(
            ProposalVersion.proposal_id == proposal_id
        )
        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0
        query = query.order_by(ProposalVersion.version_number.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count

    async def get_latest_version_number(self, proposal_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.max(ProposalVersion.version_number)).where(
                ProposalVersion.proposal_id == proposal_id
            )
        )
        return result.scalar() or 0

    async def create(self, **fields) -> ProposalVersion:
        version = ProposalVersion(**fields)
        self._session.add(version)
        await self._session.flush()
        await self._session.refresh(version)
        return version
