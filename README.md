# DevLab — Cloud-Based DevOps Learning Platform

> **Phase 3 Complete** — First Production Lab (Linux Command Line Basics) with browser-embedded terminal (xterm.js), dynamic Docker container orchestration (Docker SDK for Python), and a multi-step Validation check engine. Includes an offline Simulated terminal fallback mode.

---

## Overview

DevLab is an online platform where developers learn DevOps by launching isolated sandboxes directly from their browser. Users can launch Linux, Docker, Kubernetes, Terraform, and AWS environments with one click — each isolated per user and auto-expiring.

**Phase 3** delivers the first interactive DevOps learning course: **Linux Basics**. Users type commands directly in a responsive terminal viewport connected via WebSockets to either a live Docker container or a simulated shell environment. An automated check engine verifies their directory states, permissions, variables, and files in real-time.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (Turbopack), React 19, TypeScript, xterm.js (browser terminal) |
| **State / Data** | TanStack Query, React Hook Form, Zod |
| **Backend** | FastAPI, SQLAlchemy, Alembic, Docker SDK for Python, WebSockets |
| **Auth** | JWT (access + refresh tokens), bcrypt, Google Auth (Custom Popup selector) |
| **Database** | Neon PostgreSQL |
| **Container** | Docker Engine, Ubuntu 24.04-based student containers |

---

## Folder Structure

```
DevLab/
├── backend/                # FastAPI REST API & WebSockets
│   ├── app/
│   │   ├── api/v1/         # Route groups (auth, users, labs, labs_linux)
│   │   ├── core/           # Security keys, database config
│   │   ├── db/             # Base ORM config, initial seed fixtures
│   │   ├── dependencies/   # Current user context & DB sessions
│   │   ├── models/         # User, Lab, and LabSession SQLAlchemy models
│   │   ├── repositories/   # Base CRUD repository abstractions
│   │   ├── schemas/        # Pydantic validation structures
│   │   └── services/       # Container orchestrator & check validators
│   ├── alembic/            # DB migration revisions (lab_sessions table)
│   └── tests/              # Pytest integration checks (26 tests passing)
├── frontend/               # Next.js 16 Web App
│   ├── app/                # App Router pages (/labs, /labs/linux-basics)
│   ├── components/         # React layout shells & xterm viewport wrappers
│   └── services/           # Axios API connectors
```

---

## Lab Container Lifecycle

```
    Launch Clicked
          │
          ▼
   POST /labs/linux/launch
          │
    ┌─────┴─────┐
    ▼           ▼
[Docker Ok]  [Docker Off]
    │           │
    │ (Provision PTY Container)
    │           │
    ▼           ▼
[Docker Cont] [Simulated Directory]
    │           │
    └─────┬─────┘
          ▼
   WS /session/{id}/ws
          │
    (Terminal Active)
          │
   POST /validate (Inspect config state)
          │
   POST /stop (Destroy container/directories)
```

1. **Provisioning**: The student clicks "Launch Lab". The backend verifies there is no prior active session. It creates a `LabSession` in the database and spins up an isolated sandbox.
   * **Docker Mode**: Downloads the base Ubuntu 24.04 image, launches a memory/CPU restricted container, and creates a non-root `student` account.
   * **Simulated Mode**: Creates a temporary directory structure at `backend/scratch/sessions/{session_id}` and runs a custom Python parser to emulate Linux command outputs.
2. **WebSocket Terminal Connection**: The browser terminal component (`xterm.js`) establishes a WebSocket connection to `/api/v1/labs/linux/session/{session_id}/ws`.
   * **Docker Mode**: Direct stdin/stdout streams are bridged via a background thread listener from the running container's pseudo-terminal (PTY) socket descriptor.
   * **Simulated Mode**: Keystrokes are buffered. Carriage returns trigger local command executions which modify directories on disk and return standard prompt lines.
3. **Step Validation**: The student clicks "Verify Task" on a lesson stepper. The backend inspects files, permissions, parameters, and histories in the student's sandbox, providing immediate feedback.
4. **Termination**: When the student terminates the lab, or the 60-minute duration expires, the sandbox (container or scratch folder) is destroyed, and the session status is set to `stopped`.

---

## Database Schema updates

### `lab_sessions`
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `user_id` | UUID | FK → `users.id` (CASCADE) |
| `lab_name` | VARCHAR(100) | e.g., `"linux-basics"` |
| `container_id` | VARCHAR(128) | Nullable container ID or `"simulated-*"` |
| `status` | VARCHAR(50) | `"starting"`, `"running"`, `"stopped"`, `"expired"` |
| `started_at` | TIMESTAMPTZ | Start timestamp |
| `expires_at` | TIMESTAMPTZ | Automatic termination threshold |
| `created_at` | TIMESTAMPTZ | Record timestamp |

---

## API Endpoints

### Labs & Terminal Infrastructure
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/labs/linux/launch` | ✅ | Launches/provisions a new Linux basics sandbox container |
| POST | `/api/v1/labs/linux/{id}/stop` | ✅ | Terminates the active sandbox and cleans up resources |
| GET | `/api/v1/labs/linux/{id}/status` | ✅ | Gets status details of a specific lab session |
| GET | `/api/v1/labs/linux/active` | ✅ | Fetch the user's currently active running lab |
| GET | `/api/v1/labs/linux/sessions` | ✅ | List historical logs of user lab sessions |
| POST | `/api/v1/labs/linux/{id}/validate` | ✅ | Triggers verification check of active exercise task |
| WS | `/api/v1/labs/linux/session/{id}/ws` | — | Raw WebSocket terminal keystroke/stdout piping |

---

## Local Development Setup

### Prerequisites
- Python 3.12+
- Node.js 22+
- Docker Desktop (Optional; if missing, app falls back to Simulated Linux Sandbox Mode automatically)

### Backend

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate         # Windows
# source venv/bin/activate      # macOS/Linux

pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Seed database catalog
python app/db/seed.py

# Start API server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev       # Active at http://localhost:3000
```

---

## Running Integration Tests

Our backend is fully verified with 26 integration tests covering Authentication, Users registration, Catalog filters, dynamic session launches, and Check Engine validation routines:

```bash
cd backend
.\venv\Scripts\python -m pytest -q
```

---

## Interactive Lab Syllabus (20 Exercises)

The beginner Linuxbasics sandbox guides students through:
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

---

## License

MIT © DevLab Team
