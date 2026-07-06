"""
Request logging middleware.

Logs every incoming request and its outcome (status code, duration), and
attaches a unique request ID to both the log record and the response
headers so a single request can be traced end-to-end in aggregated logs.
"""

import logging
import time
import uuid

from app.core.security import decode_token

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        user_id = self._get_user_id(request)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.exception(
                "Unhandled exception while processing request.",
                extra={
                    "event": "request_failed",
                    "request_id": request_id,
                    "user_id": user_id,
                    "method": request.method,
                    "route": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "Request completed.",
            extra={
                "event": "request_completed",
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "route": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @staticmethod
    def _get_user_id(request: Request) -> str | None:
        authorization = request.headers.get("authorization")
        if authorization is None:
            return None

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None

        try:
            return decode_token(token).sub
        except Exception:
            return None
