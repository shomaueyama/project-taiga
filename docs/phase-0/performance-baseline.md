# Performance Baseline

## Measured

| Item | Measurement | Evidence |
|---|---:|---|
| `make lint` | 1s | Phase 0 measurement |
| `make typecheck` | 2s | Phase 0 measurement |
| `make test` | 3s | Phase 0 measurement |
| `make test-coverage` | 3s | Phase 0 measurement |
| Playwright normal | 3s | Phase 0 measurement |
| Playwright repeat x3 | 5s | Phase 0 measurement |
| Backend image | 373MB | `docker images` |
| Frontend image | 690MB | `docker images` |
| Runner controller image | 143MB | `docker images` |

## Observed Risks

- Frontend image is dev-server oriented and not optimized for production.
- Backend services use raw SQL with limited query instrumentation.
- Assignment/dashboard endpoints may duplicate assignment queries.
- Worker polling interval is fixed at 30s.
- No metrics or tracing to measure endpoint latency.
- No bundle size measurement configured.

## Not Measured

- API latency distribution.
- DB query counts.
- React render counts.
- Bundle size.
- Load under concurrency.

Target phase: Phase 5.

