"""
AI preference ORM model — settings consumed by AI proposal/scoring services.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class AIPreference(UUIDPrimaryKeyMixin, Base):
    """AI-specific configuration for a user's proposal generation and recommendations."""

    __tablename__ = "ai_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    proposal_tone: Mapped[str] = mapped_column(String(32), default="professional", nullable=False)
    proposal_length: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    writing_style: Mapped[str] = mapped_column(String(32), default="concise", nullable=False)
    automatically_include_portfolio: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    bid_recommendation_style: Mapped[str] = mapped_column(
        String(32), default="balanced", nullable=False
    )
    ai_learning_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<AIPreference user_id={self.user_id!r}>"
