"""
Global exception handlers.

Registered on the FastAPI app in `app.main`. Ensures every error response
— whether raised by our own code, a pydantic validation failure, or an
unexpected bug — has a consistent, structured JSON shape:

    {
      "error": {
        "code": "not_found",
        "message": "User not found.",
        "request_id": "..."
      }
    }
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def _error_response(request: Request, status_code: int, code: str, message: str) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the given FastAPI app."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "Application exception handled.",
            extra={
                "event": "app_exception",
                "error_code": exc.error_code,
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        return _error_response(request, exc.status_code, exc.error_code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Flatten pydantic's error list into a single readable message while
        # keeping the structured details available for API consumers.
        details = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "One or more fields failed validation.",
                    "details": details,
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_by_status = {
            status.HTTP_400_BAD_REQUEST: "bad_request",
            status.HTTP_401_UNAUTHORIZED: "authentication_error",
            status.HTTP_403_FORBIDDEN: "authorization_error",
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_409_CONFLICT: "conflict",
            status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
            status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
        }
        return _error_response(
            request,
            exc.status_code,
            code_by_status.get(exc.status_code, "http_error"),
            str(exc.detail),
        )

    @app.exception_handler(RateLimitExceeded)
    async def handle_rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return _error_response(
            request,
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception.",
            extra={
                "event": "unhandled_exception",
                "request_id": getattr(request.state, "request_id", None),
            },
        )
        return _error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_error",
            "An unexpected error occurred. Please try again later.",
        )
