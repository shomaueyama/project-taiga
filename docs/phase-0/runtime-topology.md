# Runtime Topology

## Compose Services

| Service | Image/build | Port | Healthcheck | Depends on | Volumes | Command |
|---|---|---|---|---|---|---|
| `postgres` | `postgres:17` | `5432:5432` | `pg_isready -U taiga -d taiga` | None | `postgres-data` | image default |
| `backend` | `./backend/Dockerfile` | `8000:8000` | Python HTTP `/health` | `postgres: service_healthy` | `local-storage`, read-only curriculum | Dockerfile CMD |
| `frontend` | `./frontend/Dockerfile` | `5173:5173` | None | `backend: service_healthy` | None | Dockerfile CMD |
| `worker` | `./backend/Dockerfile` | none published | None | `postgres: service_healthy` | `local-storage`, read-only curriculum, Docker socket | `python -m taiga.worker` |
| `runner-controller` | `./runner/Dockerfile` | none | None | None | read-only `local-storage`, Docker socket | `python runner_controller.py` |

## Environment Variables

- Backend/worker: `APP_ENV`, `LOCAL_AUTH_ENABLED`, `DATABASE_URL`, `LOCAL_STORAGE_ROOT`, `CURRICULUM_SOURCE_DIR`, `RUNNER_ENABLED`, `EXAM_ENABLED`, `TZ`, `VITE_API_BASE_URL`.
- Frontend: `VITE_API_BASE_URL`.
- Postgres: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `TZ`.
- Runner controller: `RUNNER_ENABLED`.

## Topology

```mermaid
flowchart TD
  Browser --> Frontend[frontend:5173]
  Frontend --> Backend[backend:8000]
  Backend --> Postgres[(postgres:5432)]
  Backend --> LocalStorage[local-storage]
  Worker --> Postgres
  Worker --> LocalStorage
  Worker --> DockerSock[/var/run/docker.sock]
  RunnerController --> DockerSock
  RunnerController --> LocalStorageRO[local-storage read-only]
```

## Runtime Risks

- No restart policies are configured.
- Worker has no healthcheck.
- Runner controller has no healthcheck and no real runner orchestration.
- Docker socket is mounted into worker and runner-controller.
- Resource limits are not configured in Compose.

