"""
MarketplaceToken ORM model - stores encrypted provider tokens.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class MarketplaceToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "marketplace_tokens"

    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("marketplace_accounts.id", ondelete="CASCADE"), nullable=False)
    token_type: Mapped[str] = mapped_column(String(32), nullable=False)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    account = relationship("MarketplaceAccount", back_populates="tokens")

    def __repr__(self) -> str:
        return f"<MarketplaceToken id={self.id} type={self.token_type!r} account_id={self.account_id}>"
