# DevLab — Cloud-Based DevOps Learning Platform

> **Phase 1 Complete** — Production-ready SaaS foundation with authentication, dashboard, and PostgreSQL.

---

## Overview

DevLab is an online platform where developers learn DevOps by launching isolated cloud sandboxes directly from their browser. Users can launch Linux, Docker, Kubernetes, Terraform, and AWS environments with one click — each isolated per user and auto-expiring.

**Phase 1** delivers the complete SaaS foundation: authentication, dashboard, profile management, PostgreSQL integration, Docker support, and CI/CD.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React, TypeScript, Tailwind CSS, shadcn/ui |
| **State / Data** | TanStack Query, React Hook Form, Zod |
| **Backend** | FastAPI, SQLAlchemy, Alembic, Pydantic |
| **Auth** | JWT (access + refresh tokens), bcrypt |
| **Database** | Neon PostgreSQL |
| **Container** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Architecture

```
DevLab/
├── backend/                # FastAPI REST API
│   ├── app/
│   │   ├── api/v1/         # Endpoint routers (auth, users)
│   │   ├── core/           # Config, security, logging
│   │   ├── db/             # SQLAlchemy session & base
│   │   ├── dependencies/   # get_db, get_current_user
│   │   ├── models/         # User, RefreshToken ORM models
│   │   ├── repositories/   # DB CRUD abstractions
│   │   ├── schemas/        # Pydantic request/response models
│   │   └── services/       # Business logic layer
│   ├── alembic/            # Database migrations
│   └── tests/              # pytest test suite
├── frontend/               # Next.js application
│   ├── app/                # App Router pages
│   ├── components/         # UI, layout, auth components
│   ├── hooks/              # useAuth React context & hook
│   ├── lib/                # Axios client with JWT interceptors
│   ├── services/           # API call functions
│   └── types/              # TypeScript interfaces
├── .github/workflows/      # GitHub Actions CI
├── docker-compose.yml      # Multi-service orchestration
└── .env.example            # Environment variables template
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | VARCHAR(255) | Required |
| email | VARCHAR(255) | Unique, indexed |
| password_hash | VARCHAR(255) | bcrypt |
| created_at | TIMESTAMPTZ | Auto |
| updated_at | TIMESTAMPTZ | Auto-updated |

### `refresh_tokens`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK → users.id (CASCADE) |
| token | VARCHAR(512) | Unique, indexed |
| expires_at | TIMESTAMPTZ | Expiry |
| is_revoked | BOOLEAN | Default false |
| created_at | TIMESTAMPTZ | Auto |

---

## API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create account |
| POST | `/api/v1/auth/login` | — | Login, get tokens |
| POST | `/api/v1/auth/refresh` | — | Rotate refresh token |
| POST | `/api/v1/auth/logout` | — | Revoke refresh token |
| GET | `/api/v1/users/me` | ✅ | Get current user |
| PUT | `/api/v1/users/me` | ✅ | Update name / password |

Swagger docs available at `http://localhost:8000/docs`

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `JWT_SECRET` | Secret key for JWT signing (change in production!) |
| `NEXT_PUBLIC_API_URL` | Backend API URL for frontend |

---

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- npm

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate         # Windows
# source venv/bin/activate      # macOS/Linux

pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

---

## Docker Setup

```bash
# Build and run all services
cp .env.example .env
docker-compose up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
# API Docs → http://localhost:8000/docs
```

---

## Running Tests

### Backend

```bash
cd backend
.\venv\Scripts\python -m pytest   # Windows
# python -m pytest                # macOS/Linux
```

### Frontend

```bash
cd frontend
npm run lint
npx tsc --noEmit
npm run build
```

---

## CI/CD

GitHub Actions runs on every push to `main` or `develop`:

1. **Backend** — pip install → flake8 lint → pytest
2. **Frontend** — npm ci → ESLint → TypeScript check → Next.js build

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## Pages

| Route | Description |
|---|---|
| `/` | Landing page |
| `/login` | Sign in |
| `/register` | Create account |
| `/dashboard` | Main workspace |
| `/profile` | Edit name & password |
| `/settings` | Theme & account settings |

---

## Future Roadmap

### Phase 2 — Lab Infrastructure
- Browser-embedded terminal (xterm.js)
- Docker container provisioning per user
- Lab timer & auto-cleanup

### Phase 3 — Content
- Linux, Docker, Kubernetes, Terraform lab modules
- Step-by-step guided exercises
- XP & progress tracking

### Phase 4 — Advanced
- AWS / Azure sandboxes
- Certificates of completion
- AI Mentor assistant
- Team workspaces

---

## License

MIT © DevLab Team
