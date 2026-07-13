import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.proposal_note import ProposalNote


class ProposalNoteRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, **fields) -> ProposalNote:
        note = ProposalNote(**fields)
        self._session.add(note)
        await self._session.flush()
        await self._session.refresh(note)
        return note

    async def get_by_id(self, note_id: uuid.UUID) -> Optional[ProposalNote]:
        result = await self._session.execute(
            select(ProposalNote).where(ProposalNote.id == note_id)
        )
        return result.scalar_one_or_none()

    async def get_by_proposal_id(
        self, proposal_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ProposalNote], int]:
        query = select(ProposalNote).where(ProposalNote.proposal_id == proposal_id)
        count_query = select(func.count(ProposalNote.id)).where(
            ProposalNote.proposal_id == proposal_id
        )
        total_result = await self._session.execute(count_query)
        total_count = total_result.scalar() or 0
        query = query.order_by(ProposalNote.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all()), total_count

    async def update(self, note: ProposalNote, **fields) -> ProposalNote:
        for key, value in fields.items():
            setattr(note, key, value)
        await self._session.flush()
        await self._session.refresh(note)
        return note

    async def delete(self, note: ProposalNote) -> None:
        await self._session.delete(note)
        await self._session.flush()
