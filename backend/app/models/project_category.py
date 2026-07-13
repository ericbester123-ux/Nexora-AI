"""
ProjectCategory ORM model.
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectCategory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A category for classifying projects (e.g. Web Development, Data Science)."""

    __tablename__ = "project_categories"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    projects = relationship("Project", secondary="project_category_links", back_populates="categories")

    def __repr__(self) -> str:
        return f"<ProjectCategory id={self.id} name={self.name!r}>"
