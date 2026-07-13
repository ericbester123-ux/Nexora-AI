import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = None
    project_type: str | None = None
    experience_level: str | None = None
    duration: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    budget_type: str | None = None
    currency: str = Field(default="USD", max_length=3)
    estimated_duration: str | None = Field(default=None, max_length=64)
    scope: str | None = Field(default=None, max_length=32)
    url: str | None = Field(default=None, max_length=1024)
    is_negotiable: bool = False
    is_remote: bool = True
    required_skills: list[str] | None = None
    is_ai_recommended: bool = False
    posted_at: datetime | None = None
    deadline: datetime | None = None


class ProjectCreate(ProjectBase):
    client_id: uuid.UUID | None = None
    external_id: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=64)
    technology_ids: list[uuid.UUID] | None = None
    category_ids: list[uuid.UUID] | None = None


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = None
    project_type: str | None = None
    experience_level: str | None = None
    duration: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    budget_type: str | None = None
    currency: str | None = Field(default=None, max_length=3)
    estimated_duration: str | None = Field(default=None, max_length=64)
    scope: str | None = Field(default=None, max_length=32)
    url: str | None = Field(default=None, max_length=1024)
    is_negotiable: bool | None = None
    is_remote: bool | None = None
    required_skills: list[str] | None = None
    is_ai_recommended: bool | None = None
    posted_at: datetime | None = None
    deadline: datetime | None = None
    client_id: uuid.UUID | None = None
    external_id: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=64)
    technology_ids: list[uuid.UUID] | None = None
    category_ids: list[uuid.UUID] | None = None


class ProjectResponse(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    client_id: uuid.UUID | None = None
    external_id: str | None = None
    platform: str | None = None
    client_rating: float | None = None
    client_reviews_count: int | None = None
    client_country: str | None = None
    client_payment_verified: bool | None = None
    client_total_spent: Decimal | None = None
    client_total_hired: int | None = None
    proposals_count: int = 0
    is_archived: bool = False
    ai_confidence_score: float | None = None
    ai_match_reason: str | None = None
    ai_recommendation_note: str | None = None
    created_at: datetime
    updated_at: datetime
    technologies: list[dict] | None = None
    categories: list[dict] | None = None

    @field_validator("technologies", mode="before")
    @classmethod
    def _convert_technologies(cls, value: Any) -> list[dict] | None:
        if value is None:
            return None
        return [
            {"id": str(t.id), "name": t.name, "slug": t.slug}
            for t in value
        ]

    @field_validator("categories", mode="before")
    @classmethod
    def _convert_categories(cls, value: Any) -> list[dict] | None:
        if value is None:
            return None
        return [
            {"id": str(c.id), "name": c.name, "slug": c.slug}
            for c in value
        ]
