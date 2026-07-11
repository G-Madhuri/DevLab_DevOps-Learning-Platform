# DevLab — Cloud-Based DevOps Learning Platform

> **Phase 4 Complete** — Docker Learning Platform + Production Foundation. Introduces modular sandbox runtimes, Upstash Redis caching and rate-limiting middleware, Nginx reverse proxying, and comprehensive user course progress tracking databases.

---

## Architecture Overview

```
                               ┌────────────────────────────────┐
                               │          User Browser          │
                               │           (xterm.js)           │
                               └───────────────┬────────────────┘
                                               │
                                       HTTP / WebSockets
                                               │
                                               ▼
                               ┌────────────────────────────────┐
                               │        Nginx Web Proxy         │
                               │ (Reverse Proxy, Gzip, Headers) │
                               └───────┬────────────────┬───────┘
                                       │                │
                             /api /ws  │                │  / (Frontend)
                                       ▼                ▼
                               ┌───────────────┐┌───────────────┐
                               │ FastAPI App   ││ Next.js App   │
                               └───────┬───────┘└───────────────┘
                                       │
                      ┌────────────────┴────────────────┐
                      ▼                                 ▼
             ┌─────────────────┐               ┌─────────────────┐
             │ Upstash Redis   │               │ Neon PostgreSQL │
             │  (REST Cache)   │               │  (Primary DB)   │
             └─────────────────┘               └─────────────────┘
                      │                                 │
         ┌────────────┴────────────┐             ┌──────┴──────┐
         ▼                         ▼             ▼             ▼
  [Active Sessions]        [Rate Limiting] [User Accounts] [Course Progress]
```

DevLab features a **Clean Architecture** layout segregating core domain abstractions, polymorphic learning runtimes, dynamic validators, and API controller router gates.

* **Modular Runtimes**: polymorphic runtimes `LinuxRuntime` and `DockerRuntime` inherit from a unified `BaseRuntime`. Docker workspaces launch nested Docker engines by mounting `/var/run/docker.sock` to student sandboxes, enabling actual Docker client instructions execution inside browser frames.
* **Upstash Redis Integrations**: a robust client parses REST commands. Includes rate-limiting (100 requests per minute per IP) and active session locking with a resilient in-memory local fallback.
* **Nginx Reverse Proxy**: standard reverse proxying for frontend Next.js server (`port 3000`), FastAPI application (`port 8000`), WebSocket handshakes upgrade headers mapping, gzip asset compression, and security headers injection.
* **PostgreSQL Progress Schema**: tracks completed lesson IDs list, percentage progression metrics, and update checkpoints per user.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (Turbopack), React 19, TypeScript, xterm.js (browser terminal) |
| **State / Data** | TanStack Query, React Hook Form, Zod |
| **Backend** | FastAPI, SQLAlchemy 2.0, Alembic, Docker SDK for Python, WebSockets |
| **Caching / Security**| Upstash Redis (REST), HTTP Rate-Limiter |
| **Proxy Gateway** | Nginx Web Server |
| **Database** | Neon PostgreSQL (Primary Storage) |
| **Containerization** | Docker Engine, Ubuntu 24.04, Docker-in-Docker |

---

## Folder Structure

```
DevLab/
├── nginx/                  # Nginx web server gateway config
│   └── nginx.conf          # Reverse proxy upstreams & compression settings
├── backend/                # FastAPI REST API & WebSockets
│   ├── app/
│   │   ├── api/v1/         # Route groups (auth, users, labs, labs_linux)
│   │   ├── core/           # Config settings, JWT, Upstash Redis client
│   │   ├── courses/        # Course definitions (Linux & Docker syllabi data)
│   │   ├── db/             # Base ORM config, database seed fixtures
│   │   ├── models/         # User, LabSession, CourseProgress ORM models
│   │   └── services/       # Modular Runtimes & check validators
│   ├── alembic/            # DB migrations (course_progress table definitions)
│   └── tests/              # Pytest verification suite (31 tests passing)
├── frontend/               # Next.js 16 Web App
│   ├── app/                # App Router pages (/dashboard, /labs, /labs/docker-basics)
│   ├── components/         # Reusable layouts & CourseViewer component
│   └── services/           # Axios API connectors
├── docker-compose.yml      # Orchestrates all multi-container services
```

---

## Environment Variables

The following parameters must be declared inside `.env` configurations:

```env
DATABASE_URL=postgresql://your_user:your_password@your_host:5432/your_db?sslmode=require
JWT_SECRET=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
NEXT_PUBLIC_API_URL=http://localhost:80/api/v1
UPSTASH_REDIS_REST_URL=https://your-upstash-redis-db.upstash.io
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_rest_token_here
```

---

## Local Development Setup

### Option 1: Docker Compose (All Services)

```bash
# 1. Start all database, caching, web server gateway, and client services
docker-compose up --build

# 2. Access the platform at http://localhost
```

### Option 2: Local Run (Manual Launch)

#### Caching (Redis)
Ensure `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN` are set in `.env` inside the `backend` folder. If they are empty, the app will run with a resilient in-memory rate-limiter and cache.

#### Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate         # Windows
# source venv/bin/activate      # macOS/Linux

pip install -r requirements.txt
alembic upgrade head
python app/db/seed.py
uvicorn app.main:app --reload --port 8000
```

#### Frontend
```bash
cd frontend
npm install
npm run dev                     # Accessible at http://localhost:3000
```

---

## Running Integration Tests

To run the complete Pytest integration suite:

```bash
cd backend
.\venv\Scripts\python -m pytest -q
```

---

## Reusable Academy Architecture

DevLab follows a clean, decoupled **Academy → Courses → Lessons → Interactive Labs → Capstone → Certificate** hierarchy. This layout is dynamic and configurations-driven to allow adding new technical tracks (e.g. AWS, Git, Terraform) without modifying database schemas or writing hardcoded route pathways.

### 1. The Configuration Blueprint (`academies.json`)
The catalog is defined inside `backend/app/courses/academies.json`. It maps all learning tracks:
- **Academy ID & Icon**: Unique slugs representing the academy (e.g. `linux`, `docker`).
- **Difficulty & Duration**: Calculated metrics per track.
- **Courses**: Child modules constituting the academy. Each has a unique `slug`, `title`, and optional `is_capstone: true` tag.

### 2. Lesson Definitions Subfolder (`lessons/`)
For each active course slug, a corresponding JSON file exists at `backend/app/courses/lessons/{course_slug}.json` containing a list of 15–20 lessons. Each lesson maps:
- `id`: unique step sequence integer.
- `title` & `definition`: core concept explanations.
- `explanation`: collapsible detail shown via Chevron toggle.
- `instruction`: explicit task description.
- `example`: runnable prompt to copy-paste.
- `expected`: verified output match pattern.
- `hint`: troubleshooting guide.
- `solution`: exact command required to pass.

### 3. Reusable Frontend CourseViewer
Workspace terminal console loops are completely modular. When a user launches any course module:
1. The frontend routes to `/labs/workspace/{course_slug}`.
2. The page dynamically mounts the `<CourseViewer>` component passing the slug.
3. The component queries `GET /{course_slug}/lessons` and `GET /{course_slug}/progress`.
4. It sets up an `xterm.js` PTY websocket bridging terminal inputs to backend container shells.

### 4. Dynamic Certificate Unlock System
The last item inside every Academy is always the Certificate slot.
- **Locked State**: Initially, the certificate is locked.
- **Verification Rule**: The backend calculates the user's progress percentage across all courses inside the academy (including the Capstone project).
- **Unlocked State**: If all courses inside the academy reach `100%` completion, the certificate is unlocked, revealing `Preview Certificate`, `Generate Certificate`, and `Download PDF` controls.

---

## Pytest Integration Suite

To run the complete validation and integration tests:

```bash
cd backend
.\venv\Scripts\python -m pytest -q
```

---

## License

MIT © DevLab Team
