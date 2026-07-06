"""
Nexora AI — FastAPI application entry point.

Wires together configuration, logging, middleware, exception handlers, and
the versioned API router. Run with:

    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.exceptions import DatabaseError
from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.logging_config import configure_logging
from app.database.session import engine
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import RequestLoggingMiddleware

settings = get_settings()

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown hooks."""
    logger.info("Starting Nexora AI backend.", extra={"event": "startup", "environment": settings.ENVIRONMENT})
    yield
    logger.info("Shutting down Nexora AI backend.", extra={"event": "shutdown"})
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered freelancer copilot API. Every AI-generated proposal, bid, "
        "or estimate requires explicit human approval before submission — "
        "the AI never submits on a user's behalf."
    ),
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# --- Rate limiting ---
app.state.limiter = limiter

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request logging (executes closest to the wire) ---
app.add_middleware(RequestLoggingMiddleware)

# --- Global exception handlers ---
register_exception_handlers(app)

# --- Versioned API routes ---
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["Health"], summary="Liveness/readiness probe")
async def health_check() -> dict:
    """Return process liveness without touching external dependencies."""
    return {"status": "ok", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}


@app.get("/ready", tags=["Health"], summary="Readiness probe")
async def readiness_check() -> dict:
    """Return readiness after verifying the database connection."""
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise DatabaseError("Database is not ready.") from exc

    return {"status": "ready", "service": settings.APP_NAME, "environment": settings.ENVIRONMENT}


@app.get("/version", tags=["Health"], summary="Application version")
async def version() -> dict:
    """Return the current application and API version metadata."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "api_prefix": settings.API_V1_PREFIX,
    }
