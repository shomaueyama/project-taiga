# Test Baseline

## Measured Commands

| Command | Duration | Result | Summary | Environment dependency |
|---|---:|---|---|---|
| `make lint` | 1s | PASS | ruff and ESLint passed | `.venv`, node_modules |
| `make typecheck` | 2s | PASS | mypy and `tsc -b` passed | `.venv`, node_modules |
| `make test` | 3s | PASS | Backend 14 passed; Frontend 1 passed | Postgres running; design pack for seed integration |
| `make validate` | <1s | PASS | Compose config and `taiga.validation` passed | Docker Compose |
| `make test-coverage` | 3s | PASS | Coverage measured | Postgres running; design pack |
| `npx playwright test` | 3s | PASS | 4 passed | Local services running |
| `npx playwright test --repeat-each=3` | 5s | PASS | 12 passed | Local services running |
| `npx playwright test --retries=2` | 2s | PASS | 4 passed | Local services running |

## Coverage

Backend total coverage from `make test-coverage`: 53%.

Frontend coverage:

- Statements: 53.27%
- Branches: 73.19%
- Functions: 21.42%
- Lines: 53.27%

## Test Inventory

- Backend unit: auth, curriculum helpers, oral review schema, runner JSON sanitization, upload validation.
- Backend integration: realistic local seed idempotency with migration.
- Frontend unit/component: Local MVP shell render.
- Playwright E2E: learner dashboard/assignment/disabled runner/exam, learner submission, admin review/admin panels, unknown local user 401.
- CI validation: backend/frontend/validation/e2e jobs.

## Test Gap Matrix

| Requirement | Unit | Integration | Component | E2E | Missing |
|---|---|---|---|---|---|
| OpenAPI parity | Partial | No | N/A | No | Contract diff |
| Full admin APIs | Partial | No | Partial UI | Partial | invite/suspend/restore/update flag |
| Exam lifecycle | Partial | Seed state | Disabled UI only | Disabled UI only | enabled exam E2E |
| Runner isolation | Minimal | No | Disabled UI | Disabled UI | hostile runner fixtures |
| Upload security | Partial | No | No | submission happy path | symlink/MIME/compression checks |
| Error handling | Minimal | No | Minimal | 401 only | 400/403/404/409/422 UI/API matrix |

