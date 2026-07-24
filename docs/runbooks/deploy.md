# Deploy Runbook

Status: manual runbook only. Do not deploy without owner approval.

## Step 1: Repository Verification

```bash
make lint
make typecheck
make test
make validate
cd frontend && npm run build
cd backend && alembic heads
docker compose config --quiet
git diff --check
git status --short
```

Confirm no secrets are tracked.

## Step 2: Neon

1. Create a Neon project.
2. Create/select the production database.
3. Store the connection string securely.
4. Add `sslmode=require` if Neon does not include it.
5. Configure Render `DATABASE_URL` and `MIGRATION_DATABASE_URL`.
6. Run:

```bash
cd backend
DATABASE_URL="<redacted>" alembic upgrade head
DATABASE_URL="<redacted>" alembic current
```

Do not paste real credentials into committed files.

## Step 3: Render

1. Create a Render Web Service from the private GitHub repository.
2. Use root directory `backend`.
3. Use build command `pip install -e ".[dev]"`.
4. Use start command `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`.
5. Configure health check `/api/health`.
6. Configure environment variables listed in `docs/deployment/cloudflare-render-neon.md`.
7. Deploy after owner approval.
8. Verify:

```text
https://api.taiganova.app/api/health
```

## Step 4: Cloudflare Pages

1. Connect Cloudflare to the private GitHub repository.
2. Select `shomaueyama/project-taiga` explicitly.
3. Root directory: `frontend`.
4. Build command: `npm install && npm run build`.
5. Output directory: `dist`.
6. Set `VITE_API_BASE_URL=https://api.taiganova.app`.
7. Deploy after owner approval.
8. Verify nested routes such as `/dashboard` and `/assignments`.

## Step 5: CORS And Authentication

1. Set Render `FRONTEND_ORIGINS=https://app.taiganova.app`.
2. Confirm no wildcard CORS is configured.
3. Protect both `app.taiganova.app` and `api.taiganova.app` with Cloudflare Access.
4. Configure Render Cloudflare Access variables through secret fields.
5. Verify authenticated API calls from the deployed frontend.

## Step 6: Two-User Acceptance Test

- Shoma account.
- Taiga account.
- Dashboard.
- Assignments.
- Submission path, with file durability limitation acknowledged.
- Review flow where applicable.
- Admin flow where applicable.
- Runner disabled state.

## Step 7: Rollback Readiness

- Record last known-good Cloudflare deployment.
- Record last known-good Render deployment.
- Record Alembic migration version.
- Confirm Neon backup/export path.

## Phase 7.4 Launch

Use `docs/deployment/production-launch.md` for the gated `taiganova.app` launch sequence.
