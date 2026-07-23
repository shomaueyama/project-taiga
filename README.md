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
make down
```

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

## Testing

```bash
make lint
make typecheck
make test
make test-coverage
cd frontend && npx playwright install
make test-e2e
cd frontend && npx playwright test --repeat-each=3
```

The current Local MVP test matrix is documented in
`docs/local-mvp-test-matrix.md`. Playwright monitors `pageerror`, `console.error`, failed requests,
and unexpected HTTP 5xx responses.

## Baseline Planning

Phase 0 baseline and planning records are in `docs/phase-0/README.md`.

## Feature Flags

Local safety defaults keep code execution and exams disabled:

```text
RUNNER_ENABLED=false
EXAM_ENABLED=false
```

The frontend renders disabled states safely and does not expose hidden tests or production
credentials.

## Local Safety Defaults

- `APP_ENV=local`
- `LOCAL_AUTH_ENABLED=true`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=false`

AWS deployment and production connections are out of scope for the Local MVP.
