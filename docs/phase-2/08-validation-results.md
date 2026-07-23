# Validation Results

Final Phase 2 validation was run on `quality/phase-2-test-coverage-reliability`.

| Command | Result | Notes |
|---|---|---|
| `make lint` baseline | PASS | Phase 1 head |
| `make typecheck` baseline | PASS | Phase 1 head |
| `make test` baseline | PASS | Backend 26, frontend 1 |
| `make test-coverage` baseline | PASS | Backend 72%, frontend statements 53.71% |
| `make validate` baseline | PASS | Phase 1 head |
| Playwright normal baseline | PASS | 4 passed |
| Playwright repeat baseline | PASS | 12 passed |
| Playwright retries baseline | PASS | 4 passed |
| `docker compose build backend worker` | PASS | backend and worker share backend Dockerfile/context |
| `docker compose up -d --build` | PASS | backend, worker, frontend, postgres, runner-controller recreated/running |
| `docker compose ps` | PASS | backend and postgres healthy; frontend, worker, runner-controller running |
| Service logs | PASS | No new 5xx or DB constraint errors after fixes and E2E |
| `make lint` final | PASS | ruff and ESLint passed |
| `make typecheck` final | PASS | mypy and TypeScript passed |
| `make test` final | PASS | Backend 39 passed; frontend 8 passed |
| `make test-coverage` final | PASS | Backend 88%; frontend statements/lines 96.69%, branches 94.73%, functions 95.34% |
| `make validate` final | PASS | Compose config and backend validation passed |
| `git diff --check` final | PASS | No whitespace errors |
| `docker compose config --quiet` final | PASS | Compose config valid |
| Playwright focused final | PASS | Reviewer revision/resubmission/approval test passed |
| Playwright normal final | PASS | 6 passed |
