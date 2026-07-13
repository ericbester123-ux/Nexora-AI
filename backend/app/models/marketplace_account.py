"""
MarketplaceAccount ORM model - stores connected marketplace accounts per user.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class MarketplaceAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketplace_accounts"

    __table_args__ = (
        Index("ix_marketplace_accounts_user_provider", "user_id", "provider"),
        Index("ix_marketplace_accounts_user_id", "user_id"),
        Index("ix_marketplace_accounts_provider_external", "provider", "external_user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    external_user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    profile_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    projects_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    member_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Sync tracking
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_status: Mapped[str] = mapped_column(String(32), default="never")
    sync_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Connection lifecycle
    connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tokens = relationship("MarketplaceToken", back_populates="account", cascade="all, delete-orphan")
    sync_history = relationship("MarketplaceSyncHistory", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<MarketplaceAccount id={self.id} provider={self.provider!r} user_id={self.user_id}>"
