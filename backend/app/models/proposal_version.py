import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


class ProposalVersion(Base):
    __tablename__ = "proposal_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(
        UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False
    )
    version_number = Column(Integer, nullable=False)
    created_by = Column(String(16), nullable=False, default="ai")
    change_summary = Column(Text, nullable=True)
    cover_letter = Column(Text, nullable=True)
    executive_summary = Column(Text, nullable=True)
    why_good_fit = Column(Text, nullable=True)
    relevant_experience = Column(Text, nullable=True)
    bid_amount = Column(Float, nullable=True)
    bid_type = Column(String(50), nullable=True)
    estimated_duration = Column(String(255), nullable=True)
    milestones = Column(Text, nullable=True)
    risk_notes = Column(Text, nullable=True)
    confidence_explanation = Column(Text, nullable=True)
    proposal_summary = Column(Text, nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    prompt_version = Column(String(50), nullable=True)
    model = Column(String(255), nullable=True)
    temperature = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    user_edits = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    proposal = relationship("Proposal", back_populates="versions")

    def __repr__(self) -> str:
        return f"<ProposalVersion {self.proposal_id} v{self.version_number}>"
