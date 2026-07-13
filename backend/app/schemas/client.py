"""
Pydantic schemas for client data.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=1024)
    country: str | None = Field(default=None, max_length=4)
    notes: str | None = Field(default=None, max_length=5000)


class ClientCreate(ClientBase):
    external_id: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=64)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=1024)
    country: str | None = Field(default=None, max_length=4)
    notes: str | None = Field(default=None, max_length=5000)
    external_id: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=64)


class ClientResponse(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    external_id: str | None = None
    platform: str | None = None
    rating: float | None = None
    total_spent: Decimal | None = None
    total_hired: int | None = None
    is_payment_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
