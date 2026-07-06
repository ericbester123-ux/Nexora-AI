"""
User preference ORM model for project discovery/matching configuration.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDPrimaryKeyMixin


class UserPreference(UUIDPrimaryKeyMixin, Base):
    """Preferences that control how Nexora recommends projects to a user."""

    __tablename__ = "user_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True, native_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    min_budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_budget: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    preferred_categories: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    preferred_technologies: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    preferred_countries: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True  # ISO 3166-1 alpha-2
    )
    preferred_languages: Mapped[list[str] | None] = mapped_column(
        JSON, nullable=True
    )
    min_client_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    require_payment_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_competition_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_daily_recommendations: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    preferred_project_age: Mapped[str | None] = mapped_column(String(16), nullable=True)
    preferred_delivery_time: Mapped[str | None] = mapped_column(String(16), nullable=True)
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
        return f"<UserPreference user_id={self.user_id!r}>"
