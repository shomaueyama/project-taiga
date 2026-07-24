# Production Launch Plan

Status: plan only. External launch steps require explicit owner approval at each gate.

## Architecture

```text
Cloudflare Access exact two-email policy
  app.taiganova.app -> Cloudflare Pages -> React/Vite
  api.taiganova.app -> Cloudflare proxied DNS -> Render Free FastAPI -> Neon Free PostgreSQL
```

Runner execution remains disabled with `RUNNER_ENABLED=false`.

## Deployment Order

1. Gate 1: purchase or configure `taiganova.app` only after price/renewal approval.
2. Gate 2: publish the approved branch and create a PR.
3. Gate 3: create Neon Free project `taiga-nova-production`.
4. Gate 4: run Alembic migrations against the approved direct Neon connection.
5. Gate 5: create Render Free service `taiga-nova-api` using `render.yaml`.
6. Gate 6: create Cloudflare Pages project `taiga-nova-web`, DNS records, custom domains, and
   Cloudflare Access applications.
7. Gate 7: run the first-user bootstrap command with owner-approved JSON.
8. Gate 8: complete smoke tests and request owner go-live acceptance.

## Service Settings

Render:

- Root directory: `backend`
- Build command: `pip install -e ".[dev]"`
- Start command: `uvicorn taiga.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/api/health`

Cloudflare Pages:

- Root directory: `frontend`
- Build command: `npm install && npm run build`
- Output directory: `dist`
- Production API URL: `https://api.taiganova.app`

Neon:

- Project: `taiga-nova-production`
- Plan: Free, unless owner explicitly approves otherwise.
- Runtime URL: pooled connection when compatible.
- Migration URL: direct connection.

## Access Policy

Create separate Cloudflare Access applications:

- `taiga-nova-web` for `app.taiganova.app`
- `taiga-nova-api` for `api.taiganova.app`

Use an Allow policy that includes exactly:

- `shomabirdie@icloud.com`
- `taiga-albatross@softbank.ne.jp`

Do not use Everyone, all valid emails, domain-wide selectors, or broad Bypass policies.

## Smoke Test Summary

- `GET https://api.taiganova.app/api/health` returns minimal 2xx.
- Unauthenticated frontend access shows Cloudflare Access before app content.
- Unauthenticated protected API access returns 401/403.
- Approved admin maps to Shoma/admin.
- Approved learner maps to Taiga/learner.
- Unauthorized emails are denied.
- CORS allows only `https://app.taiganova.app`.
- Runner remains disabled.
