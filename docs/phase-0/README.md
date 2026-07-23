# Phase 0 Baseline and Planning

Phase 0 establishes the factual baseline for Project Taiga without changing product behavior.

## Scope

- Repository state: branch `docs/phase-0-baseline-and-planning`, based on `test/local-seed-playwright-full-coverage`.
- Runtime: Docker Compose services `backend`, `worker`, `frontend`, `postgres`, `runner-controller`.
- Design pack: `../design/taiga-42-v4.0-implementation-pack`.
- Product code changes: none in this phase.

## Artifacts

- [source-of-truth.md](source-of-truth.md)
- [repository-inventory.md](repository-inventory.md)
- [architecture-baseline.md](architecture-baseline.md)
- [runtime-topology.md](runtime-topology.md)
- [frontend-inventory.md](frontend-inventory.md)
- [backend-inventory.md](backend-inventory.md)
- [database-inventory.md](database-inventory.md)
- [api-inventory.md](api-inventory.md)
- [route-inventory.md](route-inventory.md)
- [roles-permissions-matrix.md](roles-permissions-matrix.md)
- [state-machine-inventory.md](state-machine-inventory.md)
- [feature-flag-inventory.md](feature-flag-inventory.md)
- [dependency-inventory.md](dependency-inventory.md)
- [test-baseline.md](test-baseline.md)
- [ci-cd-baseline.md](ci-cd-baseline.md)
- [docker-baseline.md](docker-baseline.md)
- [security-baseline.md](security-baseline.md)
- [performance-baseline.md](performance-baseline.md)
- [ux-accessibility-baseline.md](ux-accessibility-baseline.md)
- [observability-baseline.md](observability-baseline.md)
- [technical-debt-register.md](technical-debt-register.md)
- [risk-register.md](risk-register.md)
- [unknowns-and-decisions.md](unknowns-and-decisions.md)
- [phase-1-to-8-plan.md](phase-1-to-8-plan.md)
- [phase-0-final-report.md](phase-0-final-report.md)

## Validation Snapshot

Measured locally on the Phase 0 base implementation:

- `make lint`: PASS, 1s
- `make typecheck`: PASS, 2s
- `make test`: PASS, 3s
- `make validate`: PASS, <1s
- `make test-coverage`: PASS, 3s
- `npx playwright test`: PASS, 4 tests, 3s
- `npx playwright test --repeat-each=3`: PASS, 12 tests, 5s
- `npx playwright test --retries=2`: PASS, 4 tests, 2s

