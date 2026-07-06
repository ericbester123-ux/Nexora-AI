"""
Notification preference ORM model — user opt-in/opt-out for notification types.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class NotificationPreference(UUIDPrimaryKeyMixin, Base):
    """User's notification delivery preferences. Does not implement delivery itself."""

    __tablename__ = "notification_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    high_confidence_projects: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    new_opportunities: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    messages: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_summary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    weekly_summary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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
        return f"<NotificationPreference user_id={self.user_id!r}>"
