"""
Pydantic schemas for user, AI, and notification preference configuration.
"""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ---------------------------------------------------------------------------
# User Preferences (project discovery / matching)
# ---------------------------------------------------------------------------

_SUPPORTED_CURRENCIES = {
    "USD", "EUR", "GBP", "CAD", "AUD", "INR", "JPY", "CNY", "BRL", "MXN",
    "CHF", "NZD", "SEK", "NOK", "DKK", "SGD", "HKD", "KRW", "ZAR", "TRY",
}


class UserPreferencesBase(BaseModel):
    min_budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    max_budget: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    preferred_categories: list[str] | None = None
    preferred_technologies: list[str] | None = None
    preferred_countries: list[str] | None = None
    preferred_languages: list[str] | None = None
    min_client_rating: float | None = Field(default=None, ge=0, le=5)
    require_payment_verified: bool = False
    max_competition_level: int | None = Field(default=None, ge=1, le=100)
    max_daily_recommendations: int = Field(default=10, ge=1, le=100)
    preferred_project_age: str | None = Field(default=None, max_length=16)
    preferred_delivery_time: str | None = Field(default=None, max_length=16)

    @field_validator("preferred_countries")
    @classmethod
    def _validate_country_codes(cls, value: list[str] | None) -> list[str] | None:
        if value:
            for code in value:
                if len(code) != 2 or not code.isalpha():
                    raise ValueError(f"Invalid country code: '{code}'. Use ISO 3166-1 alpha-2.")
        return [c.upper() for c in value] if value else value

    @field_validator("min_budget", "max_budget")
    @classmethod
    def _validate_budget_range(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("Budget must be non-negative.")
        return value


class UserPreferencesUpdate(UserPreferencesBase):
    pass


class UserPreferencesResponse(UserPreferencesBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID


# ---------------------------------------------------------------------------
# AI Preferences
# ---------------------------------------------------------------------------

class AIPreferencesBase(BaseModel):
    ai_enabled: bool = True
    proposal_tone: str = Field(default="professional", max_length=32)
    proposal_length: str = Field(default="medium", max_length=16)
    writing_style: str = Field(default="concise", max_length=32)
    automatically_include_portfolio: bool = True
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    bid_recommendation_style: str = Field(default="balanced", max_length=32)
    ai_learning_enabled: bool = True

    @field_validator("proposal_tone")
    @classmethod
    def _validate_tone(cls, value: str) -> str:
        allowed = {"professional", "casual", "friendly", "formal", "enthusiastic"}
        if value.lower() not in allowed:
            raise ValueError(f"proposal_tone must be one of {allowed}")
        return value.lower()

    @field_validator("proposal_length")
    @classmethod
    def _validate_length(cls, value: str) -> str:
        allowed = {"short", "medium", "long"}
        if value.lower() not in allowed:
            raise ValueError(f"proposal_length must be one of {allowed}")
        return value.lower()

    @field_validator("writing_style")
    @classmethod
    def _validate_style(cls, value: str) -> str:
        allowed = {"concise", "detailed", "storytelling", "technical", "persuasive"}
        if value.lower() not in allowed:
            raise ValueError(f"writing_style must be one of {allowed}")
        return value.lower()

    @field_validator("bid_recommendation_style")
    @classmethod
    def _validate_bid_style(cls, value: str) -> str:
        allowed = {"conservative", "balanced", "aggressive"}
        if value.lower() not in allowed:
            raise ValueError(f"bid_recommendation_style must be one of {allowed}")
        return value.lower()


class AIPreferencesUpdate(AIPreferencesBase):
    pass


class AIPreferencesResponse(AIPreferencesBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID


# ---------------------------------------------------------------------------
# Notification Preferences
# ---------------------------------------------------------------------------

class NotificationPreferencesBase(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = True
    high_confidence_projects: bool = True
    new_opportunities: bool = True
    messages: bool = True
    daily_summary: bool = True
    weekly_summary: bool = True


class NotificationPreferencesUpdate(NotificationPreferencesBase):
    pass


class NotificationPreferencesResponse(NotificationPreferencesBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
