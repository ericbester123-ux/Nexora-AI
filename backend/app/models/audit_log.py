import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(
        Uuid(as_uuid=True), ForeignKey("proposals.id", ondelete="SET NULL"), nullable=True
    )
    user_id = Column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    proposal = relationship("Proposal")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} proposal={self.proposal_id}>"
