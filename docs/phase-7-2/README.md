# Phase 7.2 Free Production Deployment Plan

Status: configuration and documentation only. No Cloudflare, Render, or Neon resources were created.

## Selected Topology

```text
Frontend: Cloudflare Pages
Backend: Render Free Web Service
Database: Neon Free PostgreSQL
Runner: Disabled
Users: Shoma and Taiga only
```

## Changes

- Frontend production API URL validation.
- Cloudflare Pages SPA fallback.
- Render service blueprint.
- Backend CORS origin configuration through `FRONTEND_ORIGINS`.
- Neon URL normalization to `postgresql+psycopg://`.
- Deployment, rollback, backup, and architecture documentation.

## Known Blockers Before Public Exposure

- Production authentication is not implemented. LocalAuth remains local-only by design.
- Render local filesystem is not durable for upload manifests.
- Seed/import flow depends on local design pack content and needs an approved production data setup.
- Render Free cold starts are expected.

## Validation Results

- `make lint`: passed.
- `make typecheck`: passed.
- `make test`: passed.
- `cd frontend && VITE_API_BASE_URL=https://api.example.invalid npm run build`: passed.
- `make validate`: passed; local Terraform CLI is not installed, so the existing Terraform target
  reported a local skip.
- `cd backend && ../.venv/bin/alembic heads`: passed.
- `cd backend && DATABASE_URL=postgresql+psycopg://taiga:taiga@localhost:5432/taiga ../.venv/bin/alembic current`: passed.
- Production settings validation with HTTPS `FRONTEND_ORIGINS` and Neon-style `postgresql://` URL:
  passed.
- `docker compose config --quiet`: passed.
- `docker compose build backend frontend`: passed.
- `git diff --check`: passed.
- Existing CI-style secret scan: passed.

Note: `cd backend && alembic current` failed when run without the project virtualenv and explicit
local `DATABASE_URL`; the shell had no global `alembic`, and the default Docker hostname `postgres`
does not resolve from the host.
