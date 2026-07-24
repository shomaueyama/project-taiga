# Phase 7.3 Production Access And Deployment

Status: Gate A complete in the repository. No Cloudflare, Render, Neon, DNS, or production data
resources were created.

## Target Topology

```text
Cloudflare Access exact two-email policy
  app.<domain> -> Cloudflare Pages frontend
  api.<domain> -> Cloudflare proxied custom hostname -> Render Free FastAPI -> Neon Free PostgreSQL
```

Runner execution remains disabled:

```text
RUNNER_ENABLED=false
```

## Repository Changes

- FastAPI validates Cloudflare Access JWTs from `Cf-Access-Jwt-Assertion` in production.
- LocalAuth remains available only when `APP_ENV=local` and `LOCAL_AUTH_ENABLED=true`.
- Production settings fail fast if Cloudflare Access configuration is missing, LocalAuth is enabled,
  Runner is enabled, the database points to local hosts, CORS is wildcard/insecure, or the allowlist
  does not contain exactly two emails.
- Public production health is limited to `GET /api/health`, returning only `{"status":"ok"}`.
- Frontend health checks use `/api/health` and display Japanese Access/cold-start errors.
- Render blueprint now uses `/api/health` and names the required Cloudflare Access env vars.

## Gate A Findings

Required owner-provided values before Gate B:

- Production domain and hostnames: `app.<domain>`, `api.<domain>`.
- Two exact authorized email addresses for `AUTHORIZED_USER_EMAILS`.
- Cloudflare Zero Trust team domain for `CLOUDFLARE_ACCESS_TEAM_DOMAIN`.
- Cloudflare Access application audience tag for `CLOUDFLARE_ACCESS_AUD`.
- Neon production connection string for `DATABASE_URL` and `MIGRATION_DATABASE_URL`.
- Render and Cloudflare project names.
- Explicit roles for the two application users.

## Stop Gates

- Gate B: create Neon, Render, Cloudflare Pages, DNS, and Access resources only after owner approval.
- Gate C: run Alembic against Neon only after confirming hostname/database and migration target.
- Gate D: first production deploy only after Access protects both frontend and API hostnames.
- Gate E: create production user rows only after owner approves exact emails and roles.

## Validation

Record the latest command results in the final Phase 7.3 report before requesting Gate B approval.
