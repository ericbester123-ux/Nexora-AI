import uuid
from typing import Optional

from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, repository: AuditLogRepository):
        self._repo = repository

    async def log(
        self,
        user_id: uuid.UUID,
        action: str,
        proposal_id: Optional[uuid.UUID] = None,
        details: Optional[str] = None,
    ):
        return await self._repo.create(
            user_id=user_id,
            action=action,
            proposal_id=proposal_id,
            details=details,
        )

    async def get_proposal_log(
        self, proposal_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list, int]:
        return await self._repo.get_by_proposal_id(
            proposal_id=proposal_id, skip=skip, limit=limit
        )
