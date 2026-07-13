"""
MarketplaceSyncHistory ORM model - tracks sync operations per account.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class MarketplaceSyncHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketplace_sync_history"

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    projects_found: Mapped[int] = mapped_column(Integer, default=0)
    projects_imported: Mapped[int] = mapped_column(Integer, default=0)
    projects_updated: Mapped[int] = mapped_column(Integer, default=0)
    projects_skipped: Mapped[int] = mapped_column(Integer, default=0)
    projects_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    account = relationship("MarketplaceAccount", back_populates="sync_history")

    def __repr__(self) -> str:
        return f"<MarketplaceSyncHistory id={self.id} status={self.status!r} account_id={self.account_id}>"
