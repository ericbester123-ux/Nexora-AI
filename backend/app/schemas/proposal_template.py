"""
Pydantic schemas for proposal templates.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProposalTemplateBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    cover_letter_template: str = Field(min_length=1)
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = None


class ProposalTemplateCreate(ProposalTemplateBase):
    pass


class ProposalTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    cover_letter_template: str | None = Field(default=None, min_length=1)
    is_default: bool | None = None
    is_active: bool | None = None
    category: str | None = Field(default=None, max_length=64)
    tags: list[str] | None = None


class ProposalTemplateResponse(ProposalTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
