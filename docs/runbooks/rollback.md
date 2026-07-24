# Rollback Runbook

Status: manual runbook only.

## Frontend Rollback

1. Open Cloudflare Pages deployments.
2. Select the last known-good deployment.
3. Promote/rollback according to Cloudflare UI.
4. Verify `/dashboard`, `/assignments`, and static asset loading.

## Backend Rollback

1. Open Render service deployments.
2. Select the last known-good deployment.
3. Redeploy that version.
4. Verify `/api/health`.

## Database Rollback

Database rollback is migration-specific. Prefer corrective migrations over destructive downgrade.

Before schema-changing deployments:

1. Record `alembic current`.
2. Export a logical backup.
3. Verify restore on a non-production database.

If rollback is needed after a migration:

1. Stop writes if possible.
2. Decide whether to apply a corrective migration or restore from backup.
3. Verify schema and application health before reopening access.

## DNS Rollback

If a custom domain was changed:

1. Revert Cloudflare DNS or Pages custom domain mapping.
2. Wait for propagation.
3. Verify Cloudflare Access still protects both hostnames.
4. Verify frontend and backend health through `/api/health`.

## Access Rollback

If an Access policy change exposes the application too broadly:

1. Revert to the last known-good Cloudflare Access policy for both `app.<domain>` and `api.<domain>`.
2. Confirm only the two approved emails are included.
3. Confirm no Bypass, Everyone, or domain-wide rule is active.
4. Confirm unauthenticated `GET /api/v1/me` returns `401`.
