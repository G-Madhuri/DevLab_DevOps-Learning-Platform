# DevLab — Cloud-Based DevOps Learning Platform

> **Phase 2 Complete** — Interactive Lab Explorer, complete seed database of 30+ DevOps exercises, search, category filters, sorting, and Google Auth integration options.

---

## Overview

DevLab is an online platform where developers learn DevOps by launching isolated cloud sandboxes directly from their browser. Users can launch Linux, Docker, Kubernetes, Terraform, and AWS environments with one click — each isolated per user and auto-expiring.

**Phase 2** delivers the main Dashboard and Lab Explorer catalog, allowing users to browse, search, sort, and filter DevOps labs in real-time.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React, TypeScript, Tailwind CSS, shadcn/ui |
| **State / Data** | TanStack Query, React Hook Form, Zod |
| **Backend** | FastAPI, SQLAlchemy, Alembic, Pydantic |
| **Auth** | JWT (access + refresh tokens), bcrypt, Google Auth (OAuth layout) |
| **Database** | Neon PostgreSQL |
| **Container** | Docker, Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Architecture

```
DevLab/
├── backend/                # FastAPI REST API
│   ├── app/
│   │   ├── api/v1/         # Endpoint routers (auth, users, labs)
│   │   ├── core/           # Config, security, logging
│   │   ├── db/             # SQLAlchemy session, base, seed.py data
│   │   ├── dependencies/   # get_db, get_current_user
│   │   ├── models/         # User, RefreshToken, Lab ORM models
│   │   ├── repositories/   # DB CRUD abstractions (user, token, lab)
│   │   ├── schemas/        # Pydantic request/response models (user, token, lab)
│   │   └── services/       # Business logic layer (auth, user, lab)
│   ├── alembic/            # Database migrations
│   └── tests/              # pytest test suite
├── frontend/               # Next.js application
│   ├── app/                # App Router pages (labs, dashboard, settings, profile)
│   ├── components/         # UI, layout, auth forms
│   ├── hooks/              # useAuth React context & hook
│   ├── lib/                # Axios client with JWT interceptors
│   ├── services/           # API call functions (auth, lab)
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

### `labs`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| title | VARCHAR(255) | Required |
| slug | VARCHAR(255) | Unique, indexed |
| description | TEXT | Detailed description |
| difficulty | VARCHAR(50) | Beginner, Intermediate, Advanced |
| duration | VARCHAR(50) | Duration (e.g. "45 minutes") |
| category | VARCHAR(50) | Linux, Docker, Kubernetes, etc. |
| icon | VARCHAR(50) | Lucide icon slug (e.g. "terminal") |
| estimated_time| VARCHAR(50) | E.g. "45m" |
| status | VARCHAR(50) | Status (e.g. "Active", "Beta") |
| coming_soon | BOOLEAN | Default true |

---

## API Endpoints

### Auth Endpoints
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/auth/register` | — | Create account |
| POST | `/api/v1/auth/login` | — | Login, get tokens |
| POST | `/api/v1/auth/refresh` | — | Rotate refresh token |
| POST | `/api/v1/auth/logout` | — | Revoke refresh token |
| GET | `/api/v1/users/me` | ✅ | Get current user |
| PUT | `/api/v1/users/me` | ✅ | Update name / password |

### Lab Endpoints
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/labs` | — | Query labs with filters, search, sort |
| GET | `/api/v1/labs/categories` | — | Fetch distinct lab categories list |
| GET | `/api/v1/labs/{slug}` | — | Get single lab detail by slug |

Swagger docs available at `http://localhost:8000/docs`

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

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

# Seed database with 30+ DevOps labs
python app/db/seed.py

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

1. **Backend** — pip install → flake8 lint → pytest (18 integration tests)
2. **Frontend** — npm ci → ESLint → TypeScript check → Next.js build

---

## Pages

| Route | Description |
|---|---|
| `/` | Landing page |
| `/login` | Sign in (Normal & Google credentials options) |
| `/register` | Create account (Normal & Google credentials options) |
| `/dashboard` | Main workspace dashboard, daily motivation quotes, upcoming features |
| `/labs` | Interactive Labs explorer, filters, sorting, categories tabs |
| `/labs/[slug]` | Syllabus curriculum details, objectives, prerequisites, banner |
| `/profile` | Edit user profile display name & password credentials |
| `/settings` | Light/Dark theme toggles and account link buttons |

---

## Future Roadmap

### Phase 3 — Lab Infrastructure
- Browser-embedded terminal (xterm.js)
- Docker container provisioning per user
- Lab timer & auto-cleanup

### Phase 4 — Progress & Content
- Automated checking engine
- Step-by-step guided exercises
- XP, Streaks & progress tracking

---

## License

MIT © DevLab Team
