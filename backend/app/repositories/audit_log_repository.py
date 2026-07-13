import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, **fields) -> AuditLog:
        entry = AuditLog(**fields)
        self._session.add(entry)
        await self._session.flush()
        await self._session.refresh(entry)
        return entry

    async def get_by_proposal_id(
        self, proposal_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLog).where(AuditLog.proposal_id == proposal_id)
        count_query = select(func.count(AuditLog.id)).where(
            AuditLog.proposal_id == proposal_id
        )
        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0
        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count
