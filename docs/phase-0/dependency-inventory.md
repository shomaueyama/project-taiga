# Dependency Inventory

## Backend Direct Dependencies

From `backend/pyproject.toml`:

- `alembic>=1.13`
- `fastapi>=0.115`
- `psycopg[binary]>=3.2`
- `pydantic>=2.8`
- `pydantic-settings>=2.4`
- `python-multipart>=0.0.9`
- `sqlalchemy>=2.0`
- `uvicorn[standard]>=0.30`

Dev:

- `httpx>=0.27`
- `mypy>=1.11`
- `pytest>=8.3`
- `pytest-cov>=6.0`
- `ruff>=0.6`
- `types-python-dateutil>=2.9`

Risk: all backend dependencies are lower-bound ranges, not pinned.

## Frontend Direct Dependencies

Observed installed versions include:

- React `19.2.8`
- React DOM `19.2.8`
- TanStack Query `5.101.4`
- React Hook Form `7.82.0`
- Zod `3.25.76`
- React Router DOM `7.18.1`
- Vite `8.1.5`
- Vitest `4.1.10`
- Playwright `1.61.1`
- TypeScript `5.9.3`

Risk: package.json uses caret ranges; lockfile controls local install but Docker `npm install` relies on lockfile.

## Infrastructure

- `python:3.13-slim` for backend/worker/runner-controller.
- `node:22-slim` for frontend.
- `postgres:17` for DB.
- GitHub Actions versions: checkout v4, setup-python v5, setup-node v4, upload-artifact v4.

## Security Notes

No vulnerability scan was run in Phase 0 beyond `npm audit` output from install showing 0 vulnerabilities. This is not a full dependency security audit.

