# Migration Plan

The migration must be incremental, reversible, and deployment-gated.

## Phase CF-0 - Assessment

- Scope: repository inspection, PostgreSQL dependency inventory, compatibility matrix, ADR.
- Deliverables: this document set under `docs/phase-7-cloudflare/` and ADR 0009.
- Entry criteria: Phase 7 branch available locally.
- Exit criteria: owner accepts or rejects Cloudflare-first direction.
- Rollback: delete assessment docs.
- Tests: existing lint/typecheck/test/validate.
- Cost implications: none.
- Owner approval required: none.

## Phase CF-1 - Local Worker Skeleton

- Scope: local Worker entry point, `/api/health`, static asset serving or proxy arrangement.
- Deliverables: `infra/cloudflare/` or `apps/worker/` skeleton, `wrangler.toml.example`, tests.
- Entry criteria: CF-0 accepted.
- Exit criteria: local Worker tests pass; no external deploy.
- Rollback: remove Worker skeleton.
- Tests: Worker unit tests, frontend build, local route smoke test.
- Cost implications: none if local-only.
- Owner approval required: before any Cloudflare login, resource creation, or deploy.

## Phase CF-2 - D1-Compatible Persistence Layer

- Scope: D1 schema conversion, migration scripts, repository abstraction, local D1 tests.
- Deliverables: D1 migration files, persistence interfaces, contract fixtures.
- Entry criteria: CF-1 complete.
- Exit criteria: representative read/write flows pass against local D1.
- Rollback: keep PostgreSQL implementation active.
- Tests: D1 migration validation, route contract tests, concurrency tests.
- Cost implications: none if local-only.
- Owner approval required: before creating any remote D1 database.

## Phase CF-3 - API Migration

- Scope: route-by-route migration from FastAPI behavior to Workers API.
- Deliverables: Worker routes for identity, dashboard, assignments, submissions, reviews, exams,
  admin read paths.
- Entry criteria: persistence abstraction available.
- Exit criteria: contract tests match current FastAPI behavior.
- Rollback: keep frontend pointed at FastAPI backend.
- Tests: contract tests, E2E against Worker local dev.
- Cost implications: none if local-only.
- Owner approval required: before preview deploy.

## Phase CF-4 - R2 And Async Processing

- Scope: uploads, object metadata, hidden tests, Queue consumers, Cron jobs.
- Deliverables: R2 abstraction, Queue producer/consumer, no runner execution.
- Entry criteria: CF-3 read/write API parity for core flows.
- Exit criteria: uploads and async status transitions work locally or in owner-approved preview.
- Rollback: keep local filesystem/PostgreSQL backend.
- Tests: upload validation, object metadata checks, Queue retry tests.
- Cost implications: remote preview may consume R2/Queue free tier.
- Owner approval required: before R2 bucket or Queue creation.

## Phase CF-5 - Preview Environment

- Scope: non-production Cloudflare preview with no production data.
- Deliverables: preview Worker/Pages deployment, preview D1/R2/Queue resources, smoke tests.
- Entry criteria: explicit owner approval and Cloudflare account setup.
- Exit criteria: smoke, accessibility, E2E, and security checks pass.
- Rollback: delete preview routes/resources after approval.
- Tests: E2E, accessibility, security headers, private repo deployment checks.
- Cost implications: likely free at low usage, but must monitor Cloudflare limits.
- Owner approval required: yes.

## Phase CF-6 - Production Cutover

- Scope: DNS cutover, monitoring, backup verification, rollback window.
- Deliverables: production deployment runbook execution, verified backup/export path.
- Entry criteria: owner approval, preview pass, rollback tested.
- Exit criteria: production smoke tests and monitoring pass.
- Rollback: return DNS/API traffic to previous backend.
- Tests: production smoke, synthetic health, audit log checks.
- Cost implications: depends on usage and Cloudflare plan limits.
- Owner approval required: yes.

## Repository Structure Recommendation

Do not move Phase 7 AWS Terraform during assessment. Recommended future organization:

```text
infra/
├── aws/
│   └── terraform foundation copied or moved after PR order is settled
└── cloudflare/
    ├── wrangler.toml.example
    └── d1/

apps/
├── web/
└── worker/

packages/
├── shared/
├── domain/
├── db/
└── api-contracts/
```

Safer interim structure: keep `frontend/` and `backend/` unchanged; add `infra/cloudflare/` plus
contract tests first. Move to `apps/` only after imports and CI are stable.

## Branching And PR Order

- Keep PR #24 as the visual stabilization base.
- Keep PR #25 as the AWS infrastructure foundation PR.
- This assessment should be a separate branch and PR after owner approval to push.
- Do not retarget or merge PR #25 automatically. Rebase/retarget only after Phase 6.75 is merged or
  the owner decides the stack order.

