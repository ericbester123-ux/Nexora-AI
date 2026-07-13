"""
Pydantic schemas for proposal data.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProposalBase(BaseModel):
    status: str = Field(default="draft", max_length=32)
    cover_letter: str | None = Field(default=None, max_length=50000)
    bid_amount: Decimal | None = None
    bid_type: str | None = Field(default=None, max_length=16)
    currency: str = Field(default="USD", max_length=3)
    estimated_duration: str | None = Field(default=None, max_length=64)
    ai_generated: bool = False
    ai_generation_version: str | None = Field(default=None, max_length=64)
    ai_confidence_score: float | None = None
    is_auto_submitted: bool = False
    requires_human_approval: bool = True


class ProposalCreate(ProposalBase):
    project_id: uuid.UUID
    template_id: uuid.UUID | None = None


class ProposalUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=32)
    cover_letter: str | None = Field(default=None, max_length=50000)
    bid_amount: Decimal | None = None
    bid_type: str | None = Field(default=None, max_length=16)
    currency: str | None = Field(default=None, max_length=3)
    estimated_duration: str | None = Field(default=None, max_length=64)
    ai_generated: bool | None = None
    ai_generation_version: str | None = Field(default=None, max_length=64)
    ai_confidence_score: float | None = None
    is_auto_submitted: bool | None = None
    requires_human_approval: bool | None = None


class ProposalResponse(ProposalBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    template_id: uuid.UUID | None = None
    human_approved_at: datetime | None = None
    submitted_at: datetime | None = None
    response_from_client: str | None = None
    client_viewed_at: datetime | None = None
    client_interview_request: bool
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime
