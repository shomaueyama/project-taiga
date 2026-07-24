# Project Taiga

Local-first learning platform MVP for Project Taiga.

This repository is implemented from the Project Taiga v4.0 Implementation Pack in:

```text
../design/taiga-42-v4.0-implementation-pack
```

The design pack is read-only. Application code, tests, migrations, and local documentation live in this repository.

## Local Targets

- Frontend: http://localhost:5173
- API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Local Routes

- `/dashboard`
- `/assignments`
- `/assignments/:assignmentId`
- `/reviews`
- `/runner`
- `/exams`
- `/admin`

## Prerequisites

- Docker and Docker Compose
- Node.js/npm for local frontend tests
- Python virtual environment at `.venv` for local backend commands
- Read-only design pack at `../design/taiga-42-v4.0-implementation-pack`

## Core Commands

```bash
make setup
docker compose up -d --build
make migrate
make seed
make lint
make typecheck
make test
make test-coverage
make test-e2e
make validate
python3 scripts/perf_load.py --scenario baseline
make down
```

## Clean Local Setup

```bash
make setup
docker compose down -v
docker compose build --no-cache
docker compose up -d
make migrate
make seed
make seed
docker compose ps
```

The second `make seed` verifies idempotency. The backend and worker use the same backend
Dockerfile. The canonical curriculum is mounted read-only from the design pack.

## Local Data

Run migration and seed after starting PostgreSQL:

```bash
docker compose up -d --build
make migrate
make seed
make seed
```

The seed is idempotent and local-only. It imports the canonical curriculum from the read-only
implementation pack and adds realistic Local MVP fixtures for:

- Admin: `admin@example.local` / 上山 捷馬
- Learner: `taiga@example.local` / 上山 虎雅
- Reviewer compatibility user: `reviewer@example.local`
- Assignment states, immutable submissions, review comments, runner job states, exam attempt states,
  rank, and capability progress

The design curriculum is mounted read-only into Docker at `/workspace/curriculum`.

To reset local data:

```bash
make reset
docker compose up -d
make migrate
make seed
```

## Testing

```bash
make lint
make typecheck
make test
make test-coverage
cd frontend && npx playwright install
make test-e2e
cd frontend && npx playwright test --repeat-each=3
cd frontend && npx playwright test --retries=2
```

The current Local MVP test matrix is documented in
`docs/local-mvp-test-matrix.md`. Playwright monitors `pageerror`, `console.error`, failed requests,
and unexpected HTTP 5xx responses.

## Baseline Planning

Phase 0 baseline and planning records are in `docs/phase-0/README.md`.
Phase 1 local MVP completion records are in `docs/phase-1/README.md`.
Phase 2 coverage/reliability records are in `docs/phase-2/`.
Phase 3 domain and architecture refactoring records are in `docs/phase-3/`.
Phase 4 security hardening records are in `docs/phase-4/`.
Phase 5 performance and scalability records are in `docs/phase-5/`.
Phase 6 UX, Japanese localization, accessibility, and responsive records are in `docs/phase-6/`.
Phase 6.5 TAIGA NOVA visual language records are in `docs/phase-6-5/`.
Phase 6.75 visual QA and layout stabilization records are in `docs/phase-6-75/`.
Phase 7 production infrastructure records are in `docs/phase-7/` and `infra/`.
Phase 7.1 Cloudflare-native assessment records are in `docs/phase-7-cloudflare/`.
Phase 7.2 free two-user deployment records are in `docs/phase-7-2/` and
`docs/deployment/cloudflare-render-neon.md`.
Phase 7.3 production Cloudflare Access controls are in `docs/phase-7-3/` and
`docs/security/cloudflare-access.md`.
Phase 7.4 gated production launch planning for `taiganova.app` is in `docs/phase-7-4/` and
`docs/deployment/production-launch.md`.

## Production Infrastructure

Phase 7 Terraform lives under `infra/` with staging and production roots. Validate without creating
AWS resources:

```bash
make terraform-validate
```

Do not run `terraform apply` until AWS account ownership, remote state, GitHub OIDC, Route53, ACM,
and rollout approval are confirmed. Production infrastructure keeps `RUNNER_ENABLED=false`.

## Feature Flags

Local safety defaults keep code execution and exams disabled:

```text
RUNNER_ENABLED=false
EXAM_ENABLED=false
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_MAX_REQUESTS=120
WORKER_IDLE_POLL_SECONDS=5
WORKER_ERROR_RETRY_SECONDS=30
```

The frontend renders disabled states safely and does not expose hidden tests or production
credentials.

When `RUNNER_ENABLED=false`, backend runner queue requests are rejected safely and no learner code is
executed. When `EXAM_ENABLED=false`, exam mutation requests are rejected safely and the frontend does
not start the exam flow. Rate limiting is local and in-process; production must replace it with a
distributed control.

## Local Safety Defaults

- `APP_ENV=local`
- `LOCAL_AUTH_ENABLED=true`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`
- `RATE_LIMIT_ENABLED=true`

AWS deployment and production connections are out of scope for the Local MVP.

The approved Phase 7.4 production topology uses Cloudflare Pages, Render Free, Neon Free, and
Cloudflare Access for exactly two users. Production launch remains gated: do not purchase domains,
create external resources, push branches, run production migrations, or deploy until the owner
approves the corresponding Phase 7.4 stop gate.

Local security hardening also includes explicit CORS methods and headers, response security headers,
strict request schema validation, generated upload storage keys, Docker socket removal from worker
services, and runner-controller container hardening. See `docs/phase-4/` for the threat model,
attack surface inventory, test matrix, and deferred risks.

Run the local read-path load test with:

```bash
python3 scripts/perf_load.py --scenario smoke
python3 scripts/perf_load.py --scenario baseline
python3 scripts/perf_load.py --scenario stress
```

The stress scenario is local-only and may intentionally hit API rate limits.

## Logs and Troubleshooting

```bash
docker compose ps
docker compose logs --tail=200
docker compose restart
docker compose down
docker compose up -d
```

If migration or seed fails, confirm PostgreSQL is healthy and the design pack path exists. If
LocalAuth fails, confirm `.env` contains `APP_ENV=local` and `LOCAL_AUTH_ENABLED=true`. LocalAuth is
intentionally rejected outside the local environment.
