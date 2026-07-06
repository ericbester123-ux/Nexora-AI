# Nexora AI — Backend

An AI-powered freelancer copilot API. The AI **never** submits proposals on
a user's behalf — every bid, proposal draft, and submission requires
explicit human approval. This repository currently implements the
**foundation**: project scaffolding, database schema, and authentication.

## Architecture

Clean Architecture with strict layer separation:

```
app/
├── main.py                    # FastAPI app assembly (composition root)
├── core/                      # Cross-cutting concerns
│   ├── config.py              # Environment-driven settings (pydantic-settings)
│   ├── security.py            # Password hashing, JWT creation/validation
│   ├── exceptions.py          # Typed application exception hierarchy
│   ├── logging_config.py      # Structured (JSON) logging setup
│   ├── limiter.py             # Rate limiter (slowapi)
│   └── dependencies.py        # FastAPI DI wiring (services, repos, current user)
├── api/v1/                    # Presentation layer — HTTP routing only
│   └── endpoints/
│       ├── auth.py            # /auth/register, /auth/login, /auth/refresh
│       └── users.py           # /users/me (GET, PATCH)
├── application/services/      # Application layer — business logic, framework-agnostic
│   ├── auth_service.py
│   └── user_service.py
├── domain/schemas/            # Pydantic request/response contracts
├── infrastructure/
│   ├── database/              # Async SQLAlchemy engine, session, declarative base
│   ├── models/                # ORM models
│   └── repositories/          # Data access layer (only layer that writes SQL/ORM queries)
└── middleware/
    ├── logging_middleware.py  # Per-request structured logging + request IDs
    └── error_handler.py       # Global exception → JSON response mapping
```

**Dependency direction**: `api` → `application` → `domain`, with
`infrastructure` implementing interfaces the application layer depends on.
Services never import FastAPI or SQLAlchemy session objects directly — they
receive repositories via constructor injection, which keeps business logic
unit-testable without a database.

## Prerequisites

- Python 3.13+
- PostgreSQL 16+ (or Docker, which provisions it for you)
- Docker & Docker Compose (recommended for local development)

## Quick Start (Docker Compose)

```bash
cp .env.example .env
# Edit .env and set a strong JWT_SECRET_KEY:
#   openssl rand -hex 32

docker compose up --build
```

This starts PostgreSQL, runs migrations automatically, and starts the API
at `http://localhost:8000`. Interactive docs: `http://localhost:8000/api/docs`.

## Quick Start (local, without Docker)

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements-dev.txt

cp .env.example .env
# Edit .env: set JWT_SECRET_KEY and point DATABASE_URL at a local Postgres instance.

# Run migrations
alembic upgrade head

# Start the API with hot reload
uvicorn app.main:app --reload
```

## Running Tests

```bash
pip install -r requirements-dev.txt
pytest -v --cov=app --cov-report=term-missing
```

Tests run against an isolated in-memory SQLite database — no external
services required. Unit tests (`tests/unit/`) test business logic and
security primitives in isolation using fakes; integration tests
(`tests/integration/`) exercise the full HTTP stack via `httpx.AsyncClient`.

## Database Migrations

Migrations are managed with Alembic and run asynchronously against
`DATABASE_URL`.

```bash
# Generate a new migration after changing ORM models
alembic revision --autogenerate -m "describe your change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

## Environment Variables

All configuration is sourced from environment variables — see
[`.env.example`](.env.example) for the authoritative list. Summary:

| Variable | Description | Required |
|---|---|---|
| `ENVIRONMENT` | `development` \| `staging` \| `production` \| `test` | Yes |
| `APP_VERSION` | Deployed application version exposed by `/version` | No |
| `JWT_SECRET_KEY` | 32+ character secret used to sign JWTs. Generate with `openssl rand -hex 32`. | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm (default `HS256`) | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | No |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | No |
| `DATABASE_URL` | Async SQLAlchemy URL, e.g. `postgresql+asyncpg://user:pass@host:5432/db` | Yes |
| `DATABASE_POOL_SIZE` / `DATABASE_MAX_OVERFLOW` | Connection pool tuning | No |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | No |
| `RATE_LIMIT_AUTH` | Rate limit for register/login (default `5/minute`) | No |
| `RATE_LIMIT_DEFAULT` | Default rate limit for other endpoints | No |
| `LOG_LEVEL` / `LOG_JSON` | Logging verbosity and format | No |

## API Overview

All endpoints are versioned under `/api/v1`. Interactive OpenAPI docs are
served at `/api/docs` (Swagger) and `/api/redoc` (ReDoc).

| Method | Path | Auth required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | No | Create an account, returns token pair |
| POST | `/api/v1/auth/login` | No | Authenticate, returns token pair |
| POST | `/api/v1/auth/refresh` | No (valid refresh token) | Rotate tokens |
| POST | `/api/v1/auth/logout` | Yes | Revoke the current access token and optional refresh token |
| GET | `/api/v1/auth/me` | Yes | Get current authenticated user |
| POST | `/api/v1/auth/password` | Yes | Change password |
| GET | `/api/v1/users/me` | Yes | Get current user's profile |
| PATCH | `/api/v1/users/me` | Yes | Update current user's profile |
| GET | `/health` | No | Liveness probe |
| GET | `/ready` | No | Readiness probe with database check |
| GET | `/version` | No | Service version metadata |

All error responses share a consistent shape:

```json
{
  "error": {
    "code": "authentication_error",
    "message": "Incorrect email or password.",
    "request_id": "b3f1c2e4-..."
  }
}
```

## Security Notes

- Passwords are hashed with bcrypt (never stored or logged in plaintext).
- JWTs are short-lived (access) with longer-lived refresh tokens; both
  carry a unique `jti` and are revoked on logout or refresh-token rotation.
- Login/register endpoints are rate-limited to mitigate credential
  stuffing and brute-force attacks.
- Error messages for authentication failures are intentionally generic to
  prevent user enumeration.
- All secrets are read from environment variables; none are hardcoded.
- CORS, request logging (with request IDs for traceability), and global
  structured error handling are configured on every request.

## What's Next

See the response accompanying this codebase for the current feature status
and recommended next steps (user/project data models, AI-powered project
analysis and proposal generation, etc.).
