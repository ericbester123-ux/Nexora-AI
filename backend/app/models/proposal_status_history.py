import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProposalStatusHistory(Base):
    __tablename__ = "proposal_status_history"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(
        Uuid(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False
    )
    from_status = Column(String(32), nullable=True)
    to_status = Column(String(32), nullable=False)
    changed_by = Column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    proposal = relationship("Proposal")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ProposalStatusHistory {self.from_status} -> {self.to_status}>"
