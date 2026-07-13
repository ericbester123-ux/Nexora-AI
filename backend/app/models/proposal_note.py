import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Text, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProposalNote(Base):
    __tablename__ = "proposal_notes"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(
        Uuid(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    proposal = relationship("Proposal")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<ProposalNote {self.id} proposal={self.proposal_id}>"
