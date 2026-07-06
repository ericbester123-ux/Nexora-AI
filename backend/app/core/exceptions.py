"""
Application-wide exception hierarchy.

Using typed exceptions (rather than raising HTTPException deep inside
services) keeps the domain/application layers free of HTTP concerns. The
FastAPI exception handlers registered in `app.middleware.error_handler`
translate these into structured HTTP responses.
"""


class AppException(Exception):
    """Base class for all application-raised exceptions."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str = "An unexpected error occurred."):
        self.message = message
        super().__init__(message)


class ValidationAppError(AppException):
    """Raised when input fails business-rule validation (distinct from
    FastAPI/pydantic schema validation, which is handled separately)."""

    status_code = 422
    error_code = "validation_error"


class BadRequestError(AppException):
    """Raised when a request is syntactically valid but semantically invalid."""

    status_code = 400
    error_code = "bad_request"


class AuthenticationError(AppException):
    """Raised when credentials are missing or invalid."""

    status_code = 401
    error_code = "authentication_error"


class InvalidTokenError(AuthenticationError):
    error_code = "invalid_token"


class TokenExpiredError(AuthenticationError):
    error_code = "token_expired"


class AuthorizationError(AppException):
    """Raised when an authenticated user lacks permission for an action."""

    status_code = 403
    error_code = "authorization_error"


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    status_code = 404
    error_code = "not_found"


class ConflictError(AppException):
    """Raised when a request conflicts with existing state (e.g. duplicate email)."""

    status_code = 409
    error_code = "conflict"


class RateLimitedError(AppException):
    """Raised when a client has exceeded an allowed rate limit."""

    status_code = 429
    error_code = "rate_limited"


class DatabaseError(AppException):
    """Raised when a database operation fails unexpectedly."""

    status_code = 503
    error_code = "database_error"


class ExternalServiceError(AppException):
    """Raised when an upstream/external service (e.g. the AI provider) fails."""

    status_code = 502
    error_code = "external_service_error"
