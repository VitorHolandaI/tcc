# Scalability Guide

This document explains the current bottlenecks that prevent running multiple instances of each service, and what needs to change to support horizontal scaling.

---

## Current State (Single-Instance)

The system runs as a single Docker Compose stack. Every service has exactly one container, and they share data through local volume mounts:

```
[Browser] → [nginx/frontend :3000]
              → [main-api :8000]       → [postgres :5432]
              → [recording-service :8001] → /app/recordings (local volume)
              → [analysis-service :8002]  → /app/webcam_recordings (local volume)
              → [webcam-service :8003]    → /app/webcam_recordings (local volume)
              → [audio-service :8004]     → /app/audio_recordings (local volume)
              → [keystroke-service :8005]
              → [similarity-service :8006]
```

This works fine for a single machine. It breaks the moment you add a second instance of any service, because:

1. The new instance has its own local filesystem — it can't see files written by the first instance.
2. WebSocket connections are stateful — a client connected to instance A can't be served by instance B.
3. PostgreSQL has a connection limit — N instances × M workers each open their own connections.

---

## Problem 1: Local File Storage

### What's happening now

Recording, webcam, and audio files are written to local directories mounted as Docker volumes:

```
./back/recordings         → /app/recordings
./back/webcam_recordings  → /app/webcam_recordings
./back/audio_recordings   → /app/audio_recordings
```

If you run two `recording-service` instances, each one writes to its own container's local filesystem. When `analysis-service` tries to read a file written by instance A, and it happens to be routed to instance B, it gets a 404.

### Fix: Shared Object Storage (MinIO or S3)

Replace local volume mounts with a shared object storage bucket. All instances read and write to the same place.

**Option A — MinIO (self-hosted, S3-compatible):**

Add to `docker-compose.yml`:
```yaml
minio:
  image: minio/minio
  container_name: testmaker-minio
  ports:
    - "9000:9000"
    - "9001:9001"  # web UI
  environment:
    - MINIO_ROOT_USER=testmaker
    - MINIO_ROOT_PASSWORD=testmaker123
  volumes:
    - minio-data:/data
  command: server /data --console-address ":9001"
  networks:
    - testmaker-network
```

Each service then uses the `boto3` (Python) or `minio` SDK to upload/download instead of `open()` on a local path.

**Option B — AWS S3:**

Same approach, but point at `s3.amazonaws.com` with proper IAM credentials. No infrastructure to manage.

**What needs to change in the code:**
- Any `open(path, "wb")` that writes a recording → replace with `s3.upload_fileobj(...)`
- Any `open(path, "rb")` that reads for analysis → replace with `s3.download_fileobj(...)`
- The `/recordings/video/{prova_id}/{aluno_id}` and similar HTTP endpoints that stream files → generate a pre-signed URL and redirect, instead of streaming from disk
- Remove all local volume mounts from `docker-compose.yml`

---

## Problem 2: Stateful WebSocket Connections

### What's happening now

The browser opens a WebSocket to `recording-service` for the duration of the exam. The recording chunks arrive in order on that one connection. If you put two `recording-service` instances behind a load balancer, the load balancer might route the next chunk to a different instance — breaking the recording.

### Fix: Sticky Sessions (short term) or Redis Pub/Sub (long term)

**Short term — sticky sessions:**

Configure your load balancer (nginx/traefik) to pin a client to the same backend instance for the duration of a session, using a cookie or the client IP. This costs nothing in code changes and works well for a small number of instances.

```nginx
upstream recording {
    ip_hash;  # pin by client IP
    server recording-service-1:8001;
    server recording-service-2:8001;
}
```

**Long term — Redis pub/sub:**

Any instance can receive a WebSocket frame, publish it to a Redis channel keyed by `(prova_id, aluno_id)`, and a single aggregator worker per recording session consumes from that channel and writes the assembled file to object storage. This decouples the WebSocket receiver from the file writer.

Add Redis to the stack:
```yaml
redis:
  image: redis:7-alpine
  container_name: testmaker-redis
  ports:
    - "6379:6379"
  networks:
    - testmaker-network
```

---

## Problem 3: Database Connection Exhaustion

### What's happening now

Each FastAPI worker opens its own SQLAlchemy connection pool. With N instances × W workers per instance, you quickly hit PostgreSQL's default `max_connections = 100`.

### Fix: PgBouncer (connection pooler)

Add PgBouncer between the services and PostgreSQL. All services connect to PgBouncer on port 5433; PgBouncer maintains a small pool of real connections to PostgreSQL.

```yaml
pgbouncer:
  image: edoburu/pgbouncer
  container_name: testmaker-pgbouncer
  environment:
    - DB_HOST=postgres
    - DB_USER=testmaker
    - DB_PASSWORD=testmaker123
    - DB_NAME=testmaker
    - POOL_MODE=transaction
    - MAX_CLIENT_CONN=1000
    - DEFAULT_POOL_SIZE=20
  depends_on:
    - postgres
  networks:
    - testmaker-network
```

Then change all service `DATABASE_URL` env vars from:
```
postgresql://testmaker:testmaker123@postgres:5432/testmaker
```
to:
```
postgresql://testmaker:testmaker123@pgbouncer:5433/testmaker
```

No code changes needed.

---

## Problem 4: Long-Running Analysis Blocks the Service

### What's happening now

When a professor triggers a video/audio/keystroke analysis, the HTTP request stays open until the analysis finishes. This ties up a worker thread for potentially minutes. With many concurrent analyses, the service becomes unresponsive.

### Fix: Task Queue (Celery + Redis)

Instead of doing analysis synchronously in the HTTP handler, enqueue it as a background job.

```
[professor clicks "Generate Analysis"]
  → POST /analysis/start
  → controller: enqueue job → Redis queue
  → return 202 Accepted immediately

[Celery worker] picks up job
  → runs analysis (1-10 minutes)
  → writes result to PostgreSQL
  → (optionally) sends a webhook/notification

[professor clicks "View Analysis"]
  → GET /analysis/result
  → controller: read from PostgreSQL
  → return result (or "still processing")
```

The `analysis-service`, `audio-service`, `keystroke-service`, and `similarity-service` are the main candidates for this pattern. The `recording-service` and `webcam-service` are real-time streaming services and don't need a task queue.

Add a Celery worker container for each analysis service. The HTTP service just enqueues; the worker processes.

---

## Problem 5: No Load Balancer in Front of Services

### What's happening now

The frontend talks directly to each service by port (`/api` → port 8000, etc.). Adding a second instance of `main-api` would require changing the frontend config.

### Fix: Reverse Proxy (nginx or Traefik)

Add a single entry-point proxy that forwards to the right backend:

```
[Browser] → [nginx :80/:443]
              /api/*          → load balance across main-api instances
              /ws/recording/* → sticky-session load balance across recording-service instances
              /               → frontend static files
```

**With Traefik (auto-discover containers):**

Traefik reads Docker labels from each container and automatically adds them to the routing table. When you scale `docker compose up --scale main-api=3`, all three instances are instantly in the load balancer pool.

```yaml
main-api:
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.main-api.rule=PathPrefix(`/api`)"
    - "traefik.http.services.main-api.loadbalancer.server.port=8000"
```

---

## Summary: What Needs to Change

| Bottleneck | Current | Fix | Code change? |
|---|---|---|---|
| File storage | Local volumes | MinIO / S3 | Yes — swap `open()` for SDK calls |
| WebSocket routing | None (single instance) | Sticky sessions | No (nginx config only) |
| DB connections | Direct pool per worker | PgBouncer | No (env var only) |
| Slow analysis | Synchronous HTTP | Celery + Redis | Yes — extract to worker tasks |
| Load balancing | None | nginx / Traefik | No (infrastructure only) |
| DB schema migrations | `create_all` on startup | Alembic | Yes — add migration runner |

---

## Migration Notes

### `create_all` is not safe with multiple instances

Currently every service calls `Base.metadata.create_all(bind=engine)` on startup. With a single instance this is fine — the first boot creates tables, subsequent boots are no-ops.

With multiple instances starting simultaneously, two instances might try to `CREATE TABLE` at the same moment, causing a race condition error (PostgreSQL will reject the duplicate `CREATE TABLE`).

**Fix:** Replace `create_all` with Alembic migrations. Migrations run once, separately from the application startup, before any service instance starts. In Docker Compose this means an `init` container that runs `alembic upgrade head` and exits before the real services start:

```yaml
db-migrate:
  build:
    context: ./back
    target: main-api
  command: alembic upgrade head
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - testmaker-network

main-api:
  depends_on:
    db-migrate:
      condition: service_completed_successfully
    ...
```

### Authentication is already stateless

Firebase JWT tokens are verified locally using the Firebase public keys — there is no session stored server-side. This means the auth layer is already horizontally scalable with zero changes.

---

## Recommended Order of Implementation

1. **PgBouncer** — zero code, immediate benefit, do this first.
2. **Alembic migrations** — required before multiple instances can safely start.
3. **MinIO / object storage** — required before scaling any recording/analysis service.
4. **nginx sticky sessions** — required before scaling `recording-service`.
5. **Celery task queue** — quality-of-life improvement for analysis throughput.
6. **Traefik** — do last, after the above are in place.
