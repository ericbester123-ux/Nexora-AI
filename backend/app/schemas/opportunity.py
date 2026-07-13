import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OpportunityBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    url: str | None = Field(default=None, max_length=1024)
    project_type: str | None = None
    experience_level: str | None = None
    duration: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    budget_type: str | None = None
    currency: str = "USD"
    skills: list[str] | None = None
    category: str | None = None
    subcategory: str | None = None
    country: str | None = Field(default=None, max_length=4)
    is_remote: bool = True
    is_negotiable: bool = False


class OpportunityCreate(OpportunityBase):
    platform: str = Field(min_length=1, max_length=64)
    external_id: str | None = Field(default=None, max_length=255)


class OpportunityUpdate(BaseModel):
    status: str | None = None
    is_ai_scored: bool | None = None
    ai_score: float | None = None
    ai_match_reason: str | None = None


class OpportunityResponse(OpportunityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    import_id: uuid.UUID | None = None
    platform: str
    external_id: str | None = None
    status: str
    client_rating: float | None = None
    client_reviews_count: int | None = None
    client_payment_verified: bool | None = None
    client_total_hired: int | None = None
    is_ai_scored: bool = False
    ai_score: float | None = None
    ai_match_reason: str | None = None
    content_hash: str | None = None
    posted_at: datetime | None = None
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ImportRequest(BaseModel):
    platform: str = Field(min_length=1, max_length=64)
    max_results: int | None = Field(default=None, ge=1, le=100)


class ImportHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    platform: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: float | None = None
    opportunities_found: int
    imported: int
    updated: int
    skipped: int
    failed: int
    status: str
    error_messages: str | None = None
    created_at: datetime


class SearchParams(BaseModel):
    keyword: str | None = None
    technology: str | None = None
    category: str | None = None
    budget_min: float | None = None
    budget_max: float | None = None
    country: str | None = None
    platform: str | None = None
    payment_verified: bool | None = None
    project_status: str | None = None
    date_posted: str | None = None


class SearchRequest(BaseModel):
    query: str = ""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    filters: dict = Field(default_factory=dict)


class ScoreResponse(BaseModel):
    opportunity_id: uuid.UUID
    score: float
    skills_score: float
    budget_score: float
    category_score: float
    experience_score: float
    client_quality_score: float
    match_reason: str


class OpportunityStatistics(BaseModel):
    total_opportunities: int
    by_platform: dict[str, int]
    by_status: dict[str, int]
    by_category: dict[str, int]
    average_budget_max: float | None = None
    total_imports: int
    last_import: datetime | None = None
