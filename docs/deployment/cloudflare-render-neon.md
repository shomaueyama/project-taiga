# Cloudflare + Render + Neon Deployment

Status: planning and configuration only. No external resources were created.

## Architecture

```text
Cloudflare Pages
  React/Vite static assets
  HTTPS/CDN/custom domain
  SPA fallback through frontend/public/_redirects

Render Free Web Service
  FastAPI via uvicorn taiga.main:app --host 0.0.0.0 --port $PORT
  Health check: /api/health
  PostgreSQL connection from DATABASE_URL

Neon Free
  PostgreSQL for SQLAlchemy and Alembic
```

Runner remains disabled:

```text
RUNNER_ENABLED=false
```

AWS Terraform under `infra/` is preserved as a future paid/enterprise deployment path.

## Repository Findings

| Area | Current state |
|---|---|
| Frontend | `frontend/`, React 19, TypeScript, Vite |
| Vite config | `frontend/vite.config.ts` |
| API base URL | `frontend/src/shared/api/client.ts`, `VITE_API_BASE_URL` |
| Backend | `backend/`, FastAPI app at `taiga.main:app` |
| Startup | `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT` for Render |
| Python packaging | `backend/pyproject.toml`, setuptools, `pip install -e ".[dev]"` |
| Database | SQLAlchemy engine from `DATABASE_URL` |
| Migrations | Alembic under `backend/alembic/` |
| CORS | `FRONTEND_ORIGINS` environment variable |
| Authentication | Cloudflare Access JWT validation in production; LocalAuth only in local |
| Health | production public endpoint is `GET /api/health` |
| File uploads | local filesystem manifest writes under `LOCAL_STORAGE_ROOT/uploads` |
| CI | `.github/workflows/ci.yml` |
| AWS infra | `infra/` preserved |
| Cloudflare native assessment | `docs/phase-7-cloudflare/` |

## Service Responsibility Matrix

| Service | Responsibility | Free-tier caveat |
|---|---|---|
| Cloudflare Pages | Frontend hosting, CDN, HTTPS, SPA fallback | Limits/pricing can change; owner must verify before production |
| Render Free | FastAPI process and health endpoint | Cold starts are expected after idle periods |
| Neon Free | PostgreSQL database | Storage/compute limits and sleep behavior require owner verification |
| Cloudflare R2 | Optional future durable upload/object storage | Not introduced in Phase 7.2 |

## Environment Variables

Names only:

### Frontend

- `VITE_API_BASE_URL`

### Backend

- `APP_ENV`
- `LOCAL_AUTH_ENABLED`
- `DATABASE_URL`
- `FRONTEND_ORIGINS`
- `RUNNER_ENABLED`
- `EXAM_ENABLED`
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_WINDOW_SECONDS`
- `RATE_LIMIT_MAX_REQUESTS`
- `WORKER_IDLE_POLL_SECONDS`
- `WORKER_ERROR_RETRY_SECONDS`
- `CLOUDFLARE_ACCESS_TEAM_DOMAIN`
- `CLOUDFLARE_ACCESS_AUD`
- `AUTHORIZED_USER_EMAILS`

## Cloudflare Pages Setup

- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Output directory: `dist`
- Production variable: `VITE_API_BASE_URL=https://api.<domain>`
- SPA fallback: `frontend/public/_redirects`

`VITE_API_BASE_URL` is required in production and must use HTTPS.

## Render Backend Setup

Use `render.yaml` or manual setup:

- Service type: Web Service
- Runtime: Python
- Root directory: `backend`
- Build command: `pip install -e ".[dev]"`
- Start command: `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`

Required Render secrets:

- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `FRONTEND_ORIGINS`
- `CLOUDFLARE_ACCESS_TEAM_DOMAIN`
- `CLOUDFLARE_ACCESS_AUD`
- `AUTHORIZED_USER_EMAILS`

Set:

- `APP_ENV=production`
- `LOCAL_AUTH_ENABLED=false`
- `RUNNER_ENABLED=false`

## Neon PostgreSQL Setup

1. Create a Neon project.
2. Create/select a production database.
3. Copy the PostgreSQL connection string.
4. Add the connection string to Render as `DATABASE_URL`.
5. Ensure SSL is required in the connection string.
6. Run Alembic migrations from an approved operator machine or one-off Render shell.
7. Verify `alembic current` and application readiness.

The backend normalizes `postgres://` and `postgresql://` URLs to SQLAlchemy's `postgresql+psycopg://`
driver form at runtime.

## Authentication

Cloudflare Access must protect both `app.<domain>` and `api.<domain>`. The backend independently
validates `Cf-Access-Jwt-Assertion` and maps only approved emails to existing application users.
Do not run production with `APP_ENV=local`.

## Cold Starts

Render Free can delay the first backend request after idle time. The frontend displays:

```text
サーバーを起動しています。初回のみ数十秒かかる場合があります。
```

Requests have a bounded frontend timeout and show a retry action instead of an infinite spinner.

## File Storage Limitation

Current upload completion writes a manifest to local disk under `LOCAL_STORAGE_ROOT/uploads`.
Render local disk is not durable storage. For Phase 7.2:

- Do not rely on uploads for durable production evidence.
- Treat upload-backed flows as limited until R2 or another durable object store is implemented.
- Keep `RUNNER_ENABLED=false`; hidden tests and generated runner artifacts must not be exposed.

## Cost And Upgrade Triggers

Target cost is approximately 0 JPY/month for two users, subject to provider free-tier changes.

Consider paid upgrade when:

- Render cold starts are frustrating.
- Backend uptime matters.
- Neon storage/compute limits are reached.
- More than two users use the system.
- Durable file uploads become important.
- Automated backups become mandatory.
- Runner execution is introduced.

Expected first paid upgrade: Render always-on backend.
