"""
Pydantic schemas for user data — the presentation/API contract, distinct
from the `User` ORM model in the infrastructure layer.
"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

_SUPPORTED_CURRENCIES = {
    "USD", "EUR", "GBP", "CAD", "AUD", "INR", "JPY", "CNY", "BRL", "MXN",
    "CHF", "NZD", "SEK", "NOK", "DKK", "SGD", "HKD", "KRW", "ZAR", "TRY",
}


class UserRole(str, Enum):
    """Supported platform roles for authorization decisions."""

    USER = "user"
    ADMIN = "admin"


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    """Payload for registering a new user."""

    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def _password_complexity(cls, value: str) -> str:
        """Enforce a minimum password complexity to reduce credential-stuffing risk."""
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit.")
        return value


class UserUpdate(BaseModel):
    """Payload for partially updating a user's profile. All fields optional."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)


class UserProfileUpdate(BaseModel):
    """Payload for replacing a user's profile (PUT /users/me)."""

    first_name: str | None = Field(default=None, max_length=128)
    last_name: str | None = Field(default=None, max_length=128)
    display_name: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, max_length=4)
    preferred_currency: str | None = Field(default=None, max_length=3)
    profile_photo_url: str | None = Field(default=None, max_length=1024)
    biography: str | None = Field(default=None, max_length=5000)
    portfolio_url: str | None = Field(default=None, max_length=1024)
    years_of_experience: int | None = Field(default=None, ge=0, le=100)
    primary_skills: list[str] | None = None
    secondary_skills: list[str] | None = None

    @field_validator("preferred_currency")
    @classmethod
    def _validate_currency(cls, value: str | None) -> str | None:
        if value and value.upper() not in _SUPPORTED_CURRENCIES:
            raise ValueError(f"Unsupported currency '{value}'. Must be a supported ISO 4217 code.")
        return value.upper() if value else value

    @field_validator("country")
    @classmethod
    def _validate_country(cls, value: str | None) -> str | None:
        if value is not None and (len(value) != 2 or not value.isalpha()):
            raise ValueError("Country must be a valid ISO 3166-1 alpha-2 code.")
        return value.upper() if value else value

    @field_validator("profile_photo_url", "portfolio_url")
    @classmethod
    def _validate_url(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class UserResponse(UserBase):
    """Public-facing representation of a user. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    subscription_status: str
    first_name: str | None = None
    last_name: str | None = None
    display_name: str | None = None
    timezone: str | None = None
    country: str | None = None
    preferred_currency: str | None = None
    profile_photo_url: str | None = None
    biography: str | None = None
    portfolio_url: str | None = None
    years_of_experience: int | None = None
    primary_skills: list[str] | None = None
    secondary_skills: list[str] | None = None
    created_at: datetime
    updated_at: datetime


class UserSubscriptionUpdate(BaseModel):
    """Payload for updating a user's subscription status."""

    subscription_status: str = Field(..., pattern="^(pending|active|cancelled|expired)$")
    is_active: bool | None = None
