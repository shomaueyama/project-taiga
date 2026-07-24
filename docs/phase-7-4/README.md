# Phase 7.4 Production Launch

Status: Gate 0 repository readiness only. No domain, Cloudflare, Render, Neon, DNS, production data,
push, PR, or deployment action has been performed.

## Confirmed Launch Targets

- Domain: `taiganova.app`
- Frontend: `https://app.taiganova.app`
- API: `https://api.taiganova.app`
- Cloudflare Pages project: `taiga-nova-web`
- Render Web Service: `taiga-nova-api`
- Neon project: `taiga-nova-production`
- Runner: disabled

Authorized production users:

| Email | Display name | Role | Timezone |
|---|---|---|---|
| `shomabirdie@icloud.com` | Shoma | admin | Asia/Tokyo |
| `taiga-albatross@softbank.ne.jp` | Taiga | learner | Asia/Tokyo |

## Gate 0 Readiness Plan

1. Verify repository state, branch, and Phase 7.3 commit.
2. Re-run local verification before any external operation.
3. Confirm production env var names and fail-closed behavior.
4. Add reproducible launch documentation without secret values.
5. Add an audited first-user bootstrap command so Gate 7 does not rely on ad hoc SQL.
6. Stop for owner approval before Gate 1.

## External Action Gates

- Gate 1: check and approve `taiganova.app` purchase price, renewal price, billing profile, and
  auto-renew behavior.
- Gate 2: approve branch publication and PR creation.
- Gate 3: approve Neon Free project/database creation and region.
- Gate 4: approve Alembic migration against Neon direct connection.
- Gate 5: approve Render Free service creation and first API deploy.
- Gate 6: approve Cloudflare Pages, DNS, custom domains, and Access applications.
- Gate 7: approve exact production user bootstrap.
- Gate 8: approve go-live acceptance after smoke tests.

## Required Production Environment Names

Values must be configured in provider secret fields or owner-approved local env injection, never in
committed files.

- `APP_ENV`
- `LOCAL_AUTH_ENABLED`
- `RUNNER_ENABLED`
- `EXAM_ENABLED`
- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `FRONTEND_ORIGINS`
- `CLOUDFLARE_ACCESS_TEAM_DOMAIN`
- `CLOUDFLARE_ACCESS_AUD`
- `AUTHORIZED_USER_EMAILS`
- `VITE_API_BASE_URL`

## Known Launch Limitations

- Render Free cold starts are accepted for the initial two-user launch.
- Render local filesystem uploads are not durable.
- Runner remains disabled; no learner code execution occurs in production.
- Recovery and backup procedures remain manual on the free-tier launch.
