# Frontend Performance

## Production Build

Command: `cd frontend && npm run build`.

| Asset | Size | Gzip |
|---|---:|---:|
| `dist/index.html` | 0.39 kB | 0.26 kB |
| CSS bundle | 2.17 kB | 0.88 kB |
| JS bundle | 389.08 kB | 116.47 kB |

## Review

- No new frontend dependency was added.
- No clearly unused frontend dependency was found during Phase 5.
- The application is still small enough that route-level code splitting would add complexity without a measured user benefit.
- Existing TanStack Query usage avoids direct component fetches and keeps request ownership in `shared/api/client.ts`.
- Initial UI requests are expected: health, local user, dashboard, assignments, progress, assignment detail; role-specific admin/reviewer queries are gated.

## Decision

No frontend bundle optimization was implemented in Phase 5. The measured gzip JS size is below the local MVP budget defined in `09_PERFORMANCE_BUDGETS.md`.
