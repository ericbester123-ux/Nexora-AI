"""
Technology ORM model.
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Technology(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A technology skill or tool available on the platform."""

    __tablename__ = "technologies"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projects = relationship("Project", secondary="project_technologies", back_populates="technologies")

    def __repr__(self) -> str:
        return f"<Technology id={self.id} name={self.name!r}>"
