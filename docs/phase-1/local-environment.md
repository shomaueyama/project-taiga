# Local Environment

Required local services are `postgres`, `backend`, `worker`, `frontend`, and `runner-controller`.

## Verified Defaults

- `APP_ENV=local`
- `LOCAL_AUTH_ENABLED=true`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`
- `VITE_API_BASE_URL=http://localhost:8000`

## Clean Workflow

```bash
make setup
docker compose down -v
docker compose build --no-cache
docker compose up -d
make migrate
make seed
make seed
docker compose ps
```

## Verification

- Clean `docker compose down -v`: PASS.
- `docker compose build --no-cache`: PASS.
- `docker compose up -d`: PASS.
- `make migrate`: PASS.
- `make seed && make seed`: PASS.
- `docker compose restart`: PASS.
- `docker compose down && docker compose up -d`: PASS.
- Final services: backend healthy, postgres healthy, frontend running, worker running,
  runner-controller running.
