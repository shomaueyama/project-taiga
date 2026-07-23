# Repository Inventory

## Structure

| Path | Responsibility | Evidence |
|---|---|---|
| `backend/` | FastAPI backend, Alembic migration, pytest tests | `backend/src/taiga/main.py`, `backend/alembic`, `backend/tests` |
| `frontend/` | React/Vite app, Vitest, Playwright | `frontend/src`, `frontend/e2e`, `frontend/package.json` |
| `runner/` | Runner controller placeholder | `runner/runner_controller.py`, `runner/Dockerfile` |
| `worker/` | Placeholder directory only | `worker/.gitkeep`; worker process builds from backend |
| `local-storage/` | Local upload/artifact/result/hidden-test directories | `.gitkeep` files and Compose bind mounts |
| `docs/` | Project docs and Phase 0 docs | `docs/github-setup.md`, `docs/phase-0` |
| `.github/workflows/` | CI workflow | `.github/workflows/ci.yml` |
| `scripts/` | Placeholder scripts directory | `scripts/.gitkeep` |
| `../design/taiga-42-v4.0-implementation-pack/` | Read-only design pack | Source of truth and contracts |

## Entrypoints

- Backend API: `uvicorn taiga.main:app --host 0.0.0.0 --port 8000` from `backend/Dockerfile`.
- Worker: `python -m taiga.worker` from `docker-compose.yml`.
- Seed: `python -m taiga.seed`.
- Migration: `alembic upgrade head`.
- Frontend dev server: `npm run dev -- --host 0.0.0.0`.
- Runner controller: `python runner_controller.py`.

## Technology Stack

| Area | Observed |
|---|---|
| Python | Host system `3.11.5`; repo venv `3.14.2`; Docker base `python:3.13-slim`; contract says Python 3.13 |
| Backend | FastAPI `0.139.2`, Pydantic `2.13.4`, SQLAlchemy `2.0.51`, Alembic `1.18.5` |
| Database | PostgreSQL `17` image |
| Frontend | React `19.2.8`, TypeScript `5.9.3`, Vite `8.1.5`, TanStack Query `5.101.4` |
| Tests | pytest, pytest-cov, Vitest `4.1.10`, RTL, Playwright `1.61.1` |
| Package managers | pip, npm |
| CI | GitHub Actions: `actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`, `actions/upload-artifact@v4` |

## Command Inventory

| Purpose | Command | Status |
|---|---|---|
| Setup | `make setup` | Exists |
| Up | `make up` or `docker compose up --build` | Exists |
| Detached up | `docker compose up -d --build` | Used for validation |
| Down | `make down` | Exists |
| Logs | `make logs` | Exists |
| Migration | `make migrate` | Exists |
| Seed | `make seed` | Exists |
| Lint | `make lint` | PASS |
| Typecheck | `make typecheck` | PASS |
| Test | `make test` | PASS |
| Coverage | `make test-coverage` | PASS |
| E2E | `make test-e2e` / `cd frontend && npx playwright test` | PASS |
| Validate | `make validate` | PASS |
| Reset | `make reset` | Exists |

## Open PR Baseline

Open Draft PRs observed:

- `#2` Phase 0 foundation
- `#4` Phase 1 database/seed
- `#6` Phase 2 auth/assignments
- `#8` Phase 3 submission/review
- `#10` Phase 4 runner
- `#12` Phase 5 exam
- `#14` Phase 6 admin operations
- `#15` seed and Playwright coverage

