# Docker Baseline

## Images

Observed local image sizes:

- `app-backend`: 373MB
- `app-worker`: 373MB
- `app-frontend`: 690MB
- `app-runner-controller`: 143MB
- `postgres:17`: 476MB

## Dockerfiles

| Dockerfile | Base | User | Multi-stage | Notes |
|---|---|---|---|---|
| `backend/Dockerfile` | `python:3.13-slim` | root | No | Copies `src` before editable install |
| `frontend/Dockerfile` | `node:22-slim` | root | No | Uses `npm install`, dev server image |
| `runner/Dockerfile` | `python:3.13-slim` | root | No | Placeholder controller |

## Known Pattern Checks

| Pattern | Baseline |
|---|---|
| source copied before editable install | Fixed in backend Dockerfile |
| bind mount overwrites app source | Only storage/curriculum mounted, not source |
| startup race | backend/worker depend on healthy postgres |
| worker exits when table missing | Worker now retries and `runner_jobs` checks `to_regclass` |
| stdout buffer | runner-controller startup print flushes |
| resource limits | NOT IMPLEMENTED |
| non-root containers | NOT IMPLEMENTED |
| read-only root filesystem | NOT IMPLEMENTED |
| runner network disabled | NOT IMPLEMENTED |

