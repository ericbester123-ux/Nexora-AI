"""
Proposal ORM model.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Proposal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A proposal submitted by a freelancer for a project."""

    __tablename__ = "proposals"

    __table_args__ = (
        Index("ix_proposals_user_status", "user_id", "status"),
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    bid_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    bid_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    estimated_duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_generation_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("proposal_templates.id", ondelete="SET NULL"), nullable=True
    )
    is_auto_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    human_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    response_from_client: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    client_interview_request: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_evaluation_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_evaluation_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    human_approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    versions: Mapped[list["ProposalVersion"]] = relationship(back_populates="proposal")

    def __repr__(self) -> str:
        return f"<Proposal id={self.id} project_id={self.project_id!r} status={self.status!r}>"
