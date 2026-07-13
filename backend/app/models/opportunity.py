import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class Opportunity(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "opportunities"

    __table_args__ = (
        Index("ix_opportunities_user_platform_external", "user_id", "platform", "external_id", unique=True),
        Index("ix_opportunities_user_id", "user_id"),
        Index("ix_opportunities_platform", "platform"),
        Index("ix_opportunities_status", "status"),
        Index("ix_opportunities_import_id", "import_id"),
        Index("ix_opportunities_content_hash", "content_hash"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    import_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("import_history.id", ondelete="SET NULL"), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="new", nullable=False)
    project_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    budget_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    subcategory: Mapped[str | None] = mapped_column(String(128), nullable=True)
    country: Mapped[str | None] = mapped_column(String(4), nullable=True)
    client_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_payment_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    client_total_hired: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ai_scored: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
