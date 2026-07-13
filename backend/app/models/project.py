import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDPrimaryKeyMixin, TimestampMixin


class ProjectTechnology(Base):
    __tablename__ = "project_technologies"

    __table_args__ = (PrimaryKeyConstraint("project_id", "technology_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    technology_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("technologies.id", ondelete="CASCADE"))


class ProjectCategoryLink(Base):
    __tablename__ = "project_category_links"

    __table_args__ = (PrimaryKeyConstraint("project_id", "category_id"),)

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("project_categories.id", ondelete="CASCADE"))


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    __table_args__ = (
        Index("ix_projects_user_status", "user_id", "status"),
        Index("ix_projects_platform_external", "platform", "external_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="open", nullable=False)
    project_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    budget_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    estimated_duration: Mapped[str | None] = mapped_column(String(64), nullable=True)
    scope: Mapped[str | None] = mapped_column(String(32), nullable=True)
    client_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    client_reviews_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    client_country: Mapped[str | None] = mapped_column(String(4), nullable=True)
    client_payment_verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    client_total_spent: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    client_total_hired: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_negotiable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    required_skills: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    proposals_count: Mapped[int] = mapped_column(Integer, default=0)
    is_ai_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_match_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_recommendation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    technologies = relationship("Technology", secondary="project_technologies", back_populates="projects")
    categories = relationship("ProjectCategory", secondary="project_category_links", back_populates="projects")
