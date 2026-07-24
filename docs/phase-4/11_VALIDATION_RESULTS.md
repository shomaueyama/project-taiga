# Validation Results

Final Phase 4 local validation was run on 2026-07-23 in `/Users/kappontomappon/Projects/project-taiga/app`.

| Command | Result | Notes |
|---|---|---|
| `make lint` | Passed | Backend ruff and frontend ESLint passed. |
| `make typecheck` | Passed | Backend mypy and frontend TypeScript passed. |
| `make test` | Passed | Backend 50 passed; frontend 8 passed. |
| `make test-coverage` | Passed | Backend 90%; frontend statements/lines 96.69%. |
| `make validate` | Passed | Compose config and backend validation passed. |
| `git diff --check` | Passed | No whitespace errors. |
| `docker compose config --quiet` | Passed | Compose file valid. |
| `cd frontend && npm run test:e2e` | Passed | Playwright 6 passed after starting backend/frontend. |
| `docker compose build` | Passed | backend, worker, frontend, runner-controller built successfully. |
| `docker compose build backend worker` | Passed | Cached rebuild passed. |
| `docker compose up -d` | Passed | All services started. |
| `docker compose ps` | Passed | backend healthy, postgres healthy, frontend/worker/runner-controller running. |
| `docker compose logs --tail=160 backend worker frontend postgres runner-controller` | Passed | Startup and E2E traffic observed; no service crash logs. |
| `npm audit` | Passed | 0 vulnerabilities. |
| Backend dependency audit | Not available | `python -m pip_audit` failed because `pip_audit` is not installed. |
| Secret scan | Reviewed | Matches were documentation terms, test attack fixtures, frontend lockfile package names, and local-only `POSTGRES_PASSWORD=taiga`; no production secret found. |

## Notes

The first E2E attempt failed because only PostgreSQL was running after the DB reset. After `docker compose build` and `docker compose up -d`, the same Playwright suite passed.
