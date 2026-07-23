# CI/CD Baseline

## Workflow

Workflow: `.github/workflows/ci.yml`.

Triggers:

- `pull_request`
- `push` to `main`

Jobs:

| Job | Purpose | Services | Cache | Artifacts | Result on PR #15 |
|---|---|---|---|---|---|
| `backend` | install, migrate, optional seed, lint, typecheck, pytest coverage | postgres:17 | none | none | PASS |
| `frontend` | install, lint, typecheck, unit test, coverage | none | npm | none | PASS |
| `e2e` | Playwright local MVP when design pack exists | Docker Compose when not skipped | npm | Playwright report on failure | PASS |
| `validation` | OpenAPI generation, schema validation, migration, Compose config, secret scan | postgres:17 | none | none | PASS |

## Local vs CI

- Local has design pack at `../design/...`; GitHub checkout does not.
- CI skips design-pack-dependent seed validation and E2E local startup when the design pack is absent.
- Local Playwright ran against active Compose services; CI E2E currently passes by skip when design pack is absent.
- Backend seed integration test skips if curriculum files are missing.

## CD

NOT IMPLEMENTED. No deployment workflow, environment protection, artifact provenance, or rollback automation exists.

## CI Risks

- No explicit permissions block.
- No timeout/concurrency settings.
- E2E skip may hide regressions in regular GitHub checkout.
- No coverage thresholds.

