# Nexora AI

AI-powered freelancer copilot. Discovers opportunities, generates proposals, evaluates readiness, and manages the review-to-submission workflow — all with human approval gates.

## Prerequisites

- **Python** 3.13+
- **Node.js** 22+
- **Docker** & **Docker Compose** (for containerised setup)
- **PostgreSQL** 16 (when running without Docker)
- **Redis** 7 (when running without Docker)

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url> nexora-ai
cd nexora-ai

# 2. Configure environment
cp backend/.env backend/.env  # already exists — just edit it

# Edit backend/.env — set JWT_SECRET_KEY and your AI provider keys
# 3. Build and start all services
docker compose up --build
```

The application becomes available at:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/docs (Swagger)
- **Health check:** http://localhost:8000/health

---

## Local Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
# Edit .env — set JWT_SECRET_KEY, DATABASE_URL, and AI provider keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

The frontend runs at http://localhost:3000.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `ENVIRONMENT` | No | `development` | `development`, `staging`, `production`, `test` |
| `JWT_SECRET_KEY` | **Yes** | — | 32+ character hex string for JWT signing |
| `DATABASE_URL` | **Yes** | — | Async SQLAlchemy database URL |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection string |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated or JSON array |
| `LLM_PROVIDER` | No | `openai` | `openai`, `claude`, `gemini`, `deepseek` |
| `OPENAI_API_KEY` | See below | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | See below | — | Anthropic API key |
| `GEMINI_API_KEY` | See below | — | Google Gemini API key |
| `DEEPSEEK_API_KEY` | See below | — | DeepSeek API key |

### Frontend (`frontend/.env.local`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | No | `http://localhost:8000/api/v1` | Backend API URL |
| `NEXT_PUBLIC_APP_NAME` | No | `Nexora AI` | Application display name |

---

## LLM Provider Configuration

Each provider requires its corresponding API key and model:

| Provider | `LLM_PROVIDER` | API Key Variable | Model Variable |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` | `LLM_MODEL` (default: `gpt-4o-mini`) |
| Claude | `claude` | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| Gemini | `gemini` | `GEMINI_API_KEY` | `GEMINI_MODEL` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL` |

The application validates the configured model at startup. If the model is missing or unavailable, it raises a clear error with instructions.

### Privacy & Data Handling

- **No automatic proposal submission:** The AI generates, improves, and evaluates proposals, but never submits them. Every submission to an external marketplace requires explicit human approval.
- **Provider choice:** All provider SDKs are lazy-loaded. You can install only the packages you need (`openai`, `anthropic`, `google-generativeai`).

---

## Running Tests

### Backend

```bash
cd backend
python -m pytest tests/ -v
```

This runs:

- **264 unit tests** — services, models, repositories, LLM providers
- **138 integration tests** — API endpoints, authentication, proposals

Total: **402 tests**.

```bash
# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=term-missing
```

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

---

## Project Structure

```
nexora-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI route handlers
│   │   ├── core/               # Config, security, exceptions
│   │   ├── infrastructure/     # LLM providers, external adapters
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── repositories/       # Data access layer
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   └── services/           # Business logic
│   ├── alembic/versions/       # Database migrations (0001-0008)
│   └── tests/
│       ├── unit/               # Unit tests
│       └── integration/        # Integration tests
├── frontend/
│   └── src/
│       ├── app/                # Next.js App Router pages
│       ├── components/         # React components (shadcn/ui)
│       ├── hooks/              # React Query hooks
│       ├── services/           # API client services
│       ├── store/              # Zustand state management
│       └── types/              # TypeScript type definitions
├── docker-compose.yml          # Root Docker Compose (all services)
└── README.md
```

---

## Key Features

- **Opportunity Discovery** — Import opportunities from multiple sources
- **AI Proposal Generation** — Generate proposals using OpenAI, Claude, Gemini, or DeepSeek
- **Proposal Improvement** — Refine proposals in 7 built-in styles or with custom instructions
- **AI Evaluation** — Score proposals on 6 axes with actionable feedback
- **Human Approval Workflow** — AI-generated proposals go through a review gate
- **Version History** — Track every change with rollback support
- **Notes & Audit Log** — Full proposal review trail

---

## API Documentation

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc

### Health Endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Liveness check |
| `GET /ready` | Readiness check (includes database) |
| `GET /version` | Application version information |

---

## Troubleshooting

### "No model configured for provider"

Set the corresponding `LLM_MODEL`, `ANTHROPIC_MODEL`, `GEMINI_MODEL`, or `DEEPSEEK_MODEL` environment variable.

### "Missing authentication credentials"

Include an `Authorization: Bearer <token>` header. Obtain a token via `POST /api/v1/auth/register` or `POST /api/v1/auth/login`.

### Database migration fails

Ensure `DATABASE_URL` points to a running database. Run `alembic upgrade head` manually to see the error.

### Frontend build fails

```bash
cd frontend
rm -rf .next node_modules package-lock.json
npm install
npm run build
```

### Docker volume permission issues

```bash
docker compose down -v
docker compose up --build
```

---

## CI/CD

GitHub Actions runs on every push:

1. Backend tests (402 tests)
2. Frontend lint + typecheck
3. Frontend production build
4. All steps must pass

---

## License

Private. All rights reserved.

## Sprint 10 — Freelancer Account Integration

### Architecture

The marketplace integration is built on a layered architecture:

```
┌─────────────────────────────────────────────┐
│              Frontend (Next.js)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │Connection│ │Dashboard │ │   Analytics   │ │
│  │  Page    │ │   Card   │ │    Page       │ │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘ │
│       │            │              │          │
│  ┌────┴────────────┴──────────────┴───────┐  │
│  │         marketplace.service.ts          │  │
│  └────────────────┬───────────────────────┘  │
└───────────────────┼──────────────────────────┘
                    │ HTTP / REST
┌───────────────────┼──────────────────────────┐
│  Backend (FastAPI)│                          │
│  ┌────────────────┴───────────────────────┐  │
│  │       /api/v1/marketplace/*            │  │
│  └────────────────┬───────────────────────┘  │
│  ┌────────────────┼───────────────────────┐  │
│  │   MarketplaceAuthService / SyncService │  │
│  └────────────────┬───────────────────────┘  │
│  ┌────────────────┼───────────────────────┐  │
│  │   MarketplaceProvider (Interface)      │  │
│  │   ┌────────────┴────────────┐         │  │
│  │   │  FreelancerProvider     │         │  │
│  │   │  (UpworkProvider)       │         │  │
│  │   │  (Future providers)     │         │  │
│  │   └─────────────────────────┘         │  │
│  └─────────────────────────────────────────┘  │
└───────────────────────────────────────────────┘
```

### Database Schema

New tables:
- **marketplace_accounts** — Connected marketplace accounts per user
- **marketplace_tokens** — Encrypted OAuth tokens per account
- **marketplace_sync_history** — Sync operation logs per account

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/marketplace/accounts` | List connected accounts |
| GET | `/api/v1/marketplace/accounts/{id}` | Get account details |
| GET | `/api/v1/marketplace/{provider}/auth-url` | Get OAuth authorization URL |
| POST | `/api/v1/marketplace/{provider}/exchange-code` | Exchange OAuth code for tokens |
| POST | `/api/v1/marketplace/{provider}/direct-connect` | Connect with existing token |
| DELETE | `/api/v1/marketplace/accounts/{id}` | Disconnect account |
| POST | `/api/v1/marketplace/accounts/{id}/reconnect` | Reconnect (token refresh) |
| POST | `/api/v1/marketplace/accounts/{id}/sync` | Trigger sync |
| GET | `/api/v1/marketplace/accounts/{id}/sync-history` | Sync history |
| GET | `/api/v1/marketplace/sync-status` | All sync statuses |
| GET | `/api/v1/marketplace/accounts/{id}/stats` | Analytics per account |

### Environment Variables

```
TOKEN_ENCRYPTION_KEY=<fernet-key>
FRONTEND_URL=http://localhost:3000
FREELANCER_CLIENT_ID=<oauth-client-id>
FREELANCER_CLIENT_SECRET=<oauth-client-secret>
```

### Testing

```bash
# Run marketplace-specific tests
pytest tests/unit/test_marketplace_models.py -v
pytest tests/unit/test_marketplace_services.py -v
```
