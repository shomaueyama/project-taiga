# First Production Launch Runbook

Status: Stop Gate A only. Do not execute external steps without owner approval.

## Gate B Checklist

1. Confirm final hostnames: `app.<domain>` and `api.<domain>`.
2. Confirm two exact authorized emails.
3. Create Neon project/database.
4. Create Render Web Service from `render.yaml`.
5. Create Cloudflare Pages project from `frontend`.
6. Add Cloudflare DNS/custom domains.
7. Create Cloudflare Access applications for both hostnames.

## Gate C Checklist

1. Confirm Neon hostname and database name without printing credentials.
2. Run:

```bash
cd backend
../.venv/bin/alembic heads
```

3. Apply migrations only after owner approval:

```bash
DATABASE_URL="$MIGRATION_DATABASE_URL" ../.venv/bin/alembic upgrade head
```

## Gate D Checklist

1. Confirm Cloudflare Access protects both hostnames.
2. Confirm Render has `APP_ENV=production`, `LOCAL_AUTH_ENABLED=false`, and `RUNNER_ENABLED=false`.
3. Confirm Cloudflare Access JWT validation is enabled by required env vars.
4. Deploy frontend with `VITE_API_BASE_URL=https://api.<domain>`.
5. Run the production smoke test.

## Gate E Checklist

Create exactly two application users through an owner-approved admin procedure. Required fields:

- Email.
- Display name.
- Role.
- Timezone.

Do not auto-create arbitrary Access-authenticated users.
