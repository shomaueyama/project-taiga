# ADR 0009: Cloudflare-Native Initial Production

## Status

Proposed.

## Context

Phase 7 added an AWS Terraform foundation, but no AWS resources were created. The owner wants TAIGA
NOVA to remain publicly available while keeping initial monthly cost as close to 0 JPY as practical.

The repository currently contains:

- React/Vite frontend in `frontend/`.
- Python FastAPI backend in `backend/src/taiga/main.py`.
- SQLAlchemy/PostgreSQL database access in `backend/src/taiga/infrastructure/database.py`.
- Alembic PostgreSQL schema under `backend/alembic/versions/`.
- Worker polling process in `backend/src/taiga/worker.py`.
- Disabled runner-controller placeholder in `runner/runner_controller.py`.

## Options

### Option 1: Existing AWS Architecture

Components: ECS Fargate, ALB, RDS PostgreSQL, S3, CloudFront, Terraform.

- Monthly cost at low usage: not close to 0 JPY because RDS, ALB, NAT, and ECS have standing cost.
- Operational complexity: highest, but production-grade and close to existing backend assumptions.
- Migration effort: lowest from current backend, because FastAPI/PostgreSQL/Docker remain valid.
- Vendor lock-in: medium AWS lock-in, mitigated by Docker/PostgreSQL portability.
- Runtime compatibility: high.
- Database compatibility: high.
- Observability: strong CloudWatch baseline.
- Security: strong network isolation possible; runner remains disabled.
- Scalability: good.
- Recovery and backup: strong with RDS snapshots.
- Future AWS path: already represented by Phase 7 Terraform.
- Current-stage suitability: too costly and operationally heavy for a near-zero-cost public release.

### Option 2: Split Free Providers

Components: Cloudflare Pages, Render or similar backend, Neon or Supabase PostgreSQL.

- Monthly cost at low usage: potentially low or free, but provider free-tier limits and suspension
  behavior require owner verification.
- Operational complexity: medium to high due to multiple providers and secrets.
- Migration effort: low to medium; FastAPI/PostgreSQL can mostly remain.
- Vendor lock-in: distributed across providers.
- Runtime compatibility: high if Python and PostgreSQL host are selected.
- Database compatibility: high.
- Observability: fragmented.
- Security: fragmented identity and network controls.
- Scalability: provider-dependent.
- Recovery and backup: provider-dependent.
- Future AWS path: easier than Cloudflare-native because PostgreSQL stays.
- Current-stage suitability: technically pragmatic, but conflicts with the preference to avoid
  managing separate frontend/backend/database providers.

### Option 3: Cloudflare-Native

Components: Worker static assets or Pages, Workers API, D1, R2, Queues/Cron where required.

- Monthly cost at low usage: best fit for near-zero-cost goal if usage stays under Cloudflare free
  limits.
- Operational complexity: potentially lowest after migration, with one Cloudflare account and
  Wrangler-based workflow.
- Migration effort: high because the Python FastAPI backend and SQLAlchemy/PostgreSQL persistence
  cannot run unchanged on Workers/D1.
- Vendor lock-in: high for Workers/D1/R2/Queues.
- Runtime compatibility: current backend is not compatible.
- Database compatibility: requires substantial schema/query migration.
- Observability: adequate for initial release but less mature than current AWS/RDS plan.
- Security: good edge controls are available, but LocalAuth must be replaced before production.
- Scalability: good for request/asset serving; D1 concurrency and size require monitoring.
- Recovery and backup: D1 Time Travel exists, but migration/export drills are still required.
- Future AWS path: preserve AWS Terraform and PostgreSQL migrations as a future scale-up path.
- Current-stage suitability: good strategic direction, not suitable for immediate rewrite-free
  production deployment.

## Decision

Proceed with a hybrid Cloudflare-first migration path:

1. Preserve the AWS Terraform foundation.
2. Do not rewrite the application immediately.
3. Start with Cloudflare assessment and local Worker skeleton in a future branch.
4. Keep PostgreSQL backend as the reference implementation until route-level parity tests exist.
5. Do not deploy externally without owner approval.

## Consequences

- The initial Cloudflare path is High effort.
- Full Cloudflare-native production is not currently suitable as an immediate next step.
- The safest next implementation step is CF-1: local-only Worker skeleton and contract-test harness.
- Production runner remains disabled.

