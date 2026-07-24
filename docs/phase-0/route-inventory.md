# Route Inventory

## Frontend Routes

| Route | Source | Behavior |
|---|---|---|
| `*` | `frontend/src/main.tsx` | Renders `App` for every browser path |

No route-specific code splitting, nested routes, or route guards are implemented.

## Backend Routes

Backend routes are documented in [api-inventory.md](api-inventory.md). All application contract routes are exposed under `/api/v1` in implementation except local `/health` and `/ready`.

## Route Gaps

| ID | Gap | Evidence | Target phase |
|---|---|---|---|
| ROUTE-001 | Frontend has no distinct URLs for dashboard, assignments, review, admin, exam, runner | `createBrowserRouter([{ path: "*", element: <App /> }])` | Phase 6 |
| ROUTE-002 | Backend path prefix differs from OpenAPI design | `main.py` routes vs OpenAPI paths | Phase 1 |
| ROUTE-003 | No 404 page or route error boundary | Frontend route wildcard | Phase 6 |

