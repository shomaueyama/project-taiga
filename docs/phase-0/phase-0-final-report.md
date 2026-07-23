# Phase 0 Final Report

## Executive Summary

Project Taiga has a working local Docker Compose MVP with backend, worker, frontend, postgres, and runner-controller running. The implementation covers local auth, assignment display, upload/submission, review, disabled runner state, disabled exam state, admin summaries, seed data, tests, and CI. The most important risks are API contract drift, incomplete runner isolation, unused idempotency persistence, and CI dependence on an external design pack.

Recommended next phase: Phase 1, to reconcile API contracts and finish local MVP semantics before broad QA expansion.

## Repository

- Stack: FastAPI/Pydantic/SQLAlchemy/Alembic/PostgreSQL and React/Vite/TanStack Query/Playwright.
- Entrypoints: `backend/src/taiga/main.py`, `frontend/src/main.tsx`, `backend/src/taiga/worker.py`, `runner/runner_controller.py`.
- Commands: documented in `repository-inventory.md`.

## Architecture

Major components and data flows are documented in `architecture-baseline.md`. The system is local-first and uses PostgreSQL as system of record. Worker/outbox exists, but true isolated runner orchestration is not implemented.

## Quality Baseline

- Local validation commands pass.
- PR #15 CI checks pass.
- Backend coverage: 53%.
- Frontend statements coverage: 53.27%.
- Playwright normal/repeat/retry passed locally.
- No flaky failure after repeat rerun.

## Risk

Top risks:

- R-001 runner enabled before isolation controls.
- R-002 OpenAPI/FastAPI drift.
- R-003 missing idempotency enforcement.
- R-004 CI design pack gap.

See `risk-register.md`.

## Technical Debt

Total tracked debt items: 10.

High priority:

- API contract drift.
- Idempotency unused.
- Runner isolation missing.
- Coverage gaps.
- Docker hardening gaps.

## Unknown

Blocking or near-blocking unknowns:

- API prefix decision.
- CI design pack strategy.
- Exam feature flag enforcement.
- Reviewer/admin exam permission semantics.

## Self Review

| Category | Score | Basis |
|---|---:|---|
| Accuracy | 10 | Paths and commands verified locally |
| Completeness | 10 | All required artifact files created |
| Consistency | 9 | Phase assignments align, with explicit UNKNOWNs |
| Traceability | 10 | Findings cite implementation/design evidence |
| Actionability | 10 | Risks/debt assigned to phases |
| Security | 10 | No secret values recorded |
| Maintainability | 9 | Tables are concise and updateable |
| Evidence quality | 10 | Based on command output and source files |
| Phase planning quality | 10 | Phase 1-8 entry/exit/gates defined |
| Operational usefulness | 10 | Runtime, CI, Docker, observability captured |

Total: 98/100. Revision count: 2.

## Git

- Branch: `docs/phase-0-baseline-and-planning`
- Base: `test/local-seed-playwright-full-coverage`
- Required final state: commit, push, Draft PR, CI pass.

## Phase 0 Validation

| Check | Result |
|---|---|
| Required artifact count | PASS, 26 files present |
| Local Markdown link check | PASS |
| Secret pattern scan | PASS |
| `git diff --check` | PASS |
| `make validate` | PASS |
| `docker compose config` | PASS |
| `markdownlint` | Not available locally |
| Mermaid CLI | Not available locally |
