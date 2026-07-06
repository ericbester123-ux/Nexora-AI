"""
Pydantic schemas for the authentication API surface.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseModel):
    """Optional refresh token to revoke alongside the bearer access token."""

    refresh_token: str | None = Field(default=None, min_length=1)


class PasswordChangeRequest(BaseModel):
    """Payload for changing the authenticated user's password."""

    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _password_complexity(cls, value: str) -> str:
        """Enforce password complexity for newly chosen passwords."""
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit.")
        return value


class TokenResponse(BaseModel):
    """Standard OAuth2-style token pair returned on login/register/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifetime in seconds.")


class MessageResponse(BaseModel):
    """Simple success response for command-style auth endpoints."""

    message: str
