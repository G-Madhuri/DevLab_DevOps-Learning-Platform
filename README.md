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

## Reusable Course Syllabus

### Course 1: Linux Basics (20 Exercises)
1. **Navigation** (`pwd`)
2. **Working Directories** (`ls -a`)
3. **Files** (`touch note.txt`)
4. **Directories** (`mkdir backup`)
5. **Copy** (`cp note.txt backup/note_copy.txt`)
6. **Move** (`mv backup/note_copy.txt .`)
7. **Rename** (`mv note_copy.txt log.txt`)
8. **Delete** (`rm note.txt`)
9. **Viewing Files** (`cat log.txt`)
10. **Permissions** (`chmod 600 log.txt`)
11. **Users** (`id`)
12. **Groups** (`groups`)
13. **Searching** (`grep student log.txt`)
14. **Pipes** (`ls | grep log.txt`)
15. **Redirection** (`echo "DevOps" > dynamic.txt`)
16. **Environment Variables** (`export REGISTRY=local`)
17. **Processes** (`ps`)
18. **Networking** (`ip route`)
19. **Directory Deletions** (`rm -rf backup`)
20. **Workspace Cleanup** (`ls -la`)

### Course 2: Docker Basics (18 Exercises)
1. **Docker Introduction** (`docker --version`)
2. **Docker Architecture** (`docker info`)
3. **Docker Installation Check** (`docker run hello-world`)
4. **Images** (`docker pull alpine` & `docker images`)
5. **Containers** (`docker run -d --name my_web nginx`)
6. **Docker CLI** (`docker ps -a`)
7. **Dockerfile** (Write base instructions)
8. **Build & Layers** (`docker build -t custom_app:v1 .`)
9. **Build Cache** (cached layer verification)
10. **Volumes** (`docker volume create db_data`)
11. **Networks** (`docker network create backend_net`)
12. **Environment Variables** (`docker run -d -e PORT=8080 nginx`)
13. **Logs** (`docker logs my_web`)
14. **Exec** (`docker exec my_web date`)
15. **Inspect** (`docker inspect bridge`)
16. **Multi-stage Builds** (COPY --from instructions)
17. **Stop & Cleanup** (`docker stop my_web` & `docker rm my_web`)
18. **Final Project** (docker-compose YAML aggregations)

---

## License

MIT © DevLab Team
