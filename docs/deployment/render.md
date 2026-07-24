# Render Backend Deployment

Status: plan only. No Render service was created.

## Service

Use the checked-in `render.yaml`.

- Runtime: Python.
- Root directory: `backend`.
- Build command: `pip install -e ".[dev]"`.
- Start command: `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`.
- Health check path: `/api/health`.

Required environment variables:

- `APP_ENV=production`
- `LOCAL_AUTH_ENABLED=false`
- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `FRONTEND_ORIGINS=https://app.<domain>`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`
- `RATE_LIMIT_ENABLED=true`
- `CLOUDFLARE_ACCESS_TEAM_DOMAIN`
- `CLOUDFLARE_ACCESS_AUD`
- `AUTHORIZED_USER_EMAILS`

## Custom Hostname

Expose the API through Cloudflare as `api.<domain>`. The raw Render hostname may serve
`GET /api/health`, but authenticated application access must still fail without a valid
`Cf-Access-Jwt-Assertion`.

## Cold Starts

Render Free may sleep after idle periods. The frontend shows a bounded Japanese retry state for
timeouts and server errors.

Official references:

- https://render.com/docs/deploy-fastapi
- https://render.com/docs/health-checks
- https://render.com/docs/web-services
- https://render.com/docs/rollbacks
