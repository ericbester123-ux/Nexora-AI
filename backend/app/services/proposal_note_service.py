import uuid
from typing import Optional

from app.core.exceptions import AuthorizationError, NotFoundError
from app.models.proposal_note import ProposalNote
from app.repositories.proposal_note_repository import ProposalNoteRepository


class ProposalNoteService:
    def __init__(self, repository: ProposalNoteRepository):
        self._repo = repository

    async def create(
        self, proposal_id: uuid.UUID, user_id: uuid.UUID, content: str
    ) -> ProposalNote:
        return await self._repo.create(
            proposal_id=proposal_id,
            user_id=user_id,
            content=content,
        )

    async def get_by_id(
        self, note_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> ProposalNote:
        note = await self._repo.get_by_id(note_id)
        if note is None:
            raise NotFoundError("Note not found.")
        if user_id is not None and note.user_id != user_id:
            raise AuthorizationError("You do not have permission to access this note.")
        return note

    async def get_by_proposal_id(
        self, proposal_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[ProposalNote], int]:
        return await self._repo.get_by_proposal_id(
            proposal_id=proposal_id, skip=skip, limit=limit
        )

    async def update(
        self, note_id: uuid.UUID, user_id: uuid.UUID, content: str
    ) -> ProposalNote:
        note = await self.get_by_id(note_id, user_id=user_id)
        return await self._repo.update(note, content=content)

    async def delete(self, note_id: uuid.UUID, user_id: uuid.UUID) -> None:
        note = await self.get_by_id(note_id, user_id=user_id)
        await self._repo.delete(note)
