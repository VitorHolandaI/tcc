# Docker Compose Guide

## Two Modes

### 1. Full stack (production-like)
All services + frontend in containers.

```bash
docker compose up --build
```

Access at `http://localhost:3000`.

### 2. DB only (local development)
Only PostgreSQL runs in Docker. Services run natively on your machine.

```bash
docker compose -f docker-compose.db.yml up -d
```

Connection string: `postgresql://testmaker:testmaker123@localhost:5432/testmaker`

---

## Container Names and Ports

| Container | Service | Port |
|---|---|---|
| `testmaker-db` | PostgreSQL | 5432 |
| `testmaker-main-api` | Main API | 8000 |
| `testmaker-recording` | Recording | 8001 |
| `testmaker-analysis` | Video/Gaze analysis | 8002 |
| `testmaker-webcam` | Webcam | 8003 |
| `testmaker-audio` | Audio (`dbc`) | 8004 |
| `testmaker-keystroke` | Keystroke | 8005 |
| `testmaker-similarity` | Similarity | 8006 |
| `testmaker-frontend` | Frontend (nginx) | 3000 |

---

## Required `.env` (root of project)

```env
FIREBASE_PROJECT_ID=your-project-id
HUGGINGFACE_TOKEN=hf_...
```

The Firebase service account JSON file must exist at:
`back/corretor-9dcf3-firebase-adminsdk-fbsvc-3c2575a3b8.json`

---

## Common Commands

```bash
# Start everything (rebuild images)
docker compose up --build

# Start in background
docker compose up --build -d

# Stop and remove containers (keeps volumes)
docker compose down

# Stop and wipe the database volume
docker compose down -v

# Rebuild and restart a single service
docker compose up --build audio-service

# View logs for all services
docker compose logs -f

# View logs for one service
docker compose logs -f audio-service

# Check container status
docker compose ps
```

---

## Debugging a Failing Container

```bash
# See what's crashing (replace <name> with container name from table above)
docker logs testmaker-audio

# Follow live logs
docker logs -f testmaker-audio

# Open a shell inside a running container
docker exec -it testmaker-audio bash

# Check health status
docker inspect testmaker-audio | grep -A 5 Health
```

---

## Database Operations

```bash
# Connect to PostgreSQL directly
docker exec -it testmaker-db psql -U testmaker -d testmaker

# Drop and recreate all tables (wipes all data)
docker compose down -v
docker compose up --build -d postgres
# Then restart the other services so create_all runs again
docker compose up --build -d
```

> The project uses `Base.metadata.create_all()` — there are no Alembic migrations. Adding or changing model columns requires dropping and recreating the tables.

---

## Build Notes

- `main-api` and `recording-service` are built from `./back` using multi-stage targets (`target: main-api`, `target: recording-service`) defined in `back/Dockerfile`.
- All other services have their own `Dockerfile` inside their subdirectory (e.g. `back/audio-service/Dockerfile`).
- Frontend is built from `./front` and served via nginx on port 3000.
- All services share the `testmaker-network` bridge network, so they reach each other by service name (e.g. `http://audio-service:8004`).
- Shared data directories are mounted as volumes: `recordings/`, `webcam_recordings/`, `audio_recordings/`, `data/`, `logs/`.
