# Frontend Inventory

## Routes

| Route | Component | Required role | Data source | Loading | Empty | Error | Feature flag | Test |
|---|---|---|---|---|---|---|---|---|
| `*` | `App` | Local user if signed in | `/health`, `/me`, `/dashboard`, `/assignments`, `/progress`, `/exams`, admin/review APIs | Implicit React Query pending text/counts | Counts and fallback text | Minimal: failed `me` shows `Not signed in`; query errors mostly implicit | Health fields `runner_enabled`, `exam_enabled`; DB flags for admin display | `App.test.tsx`, `local-mvp.spec.ts` |

No multi-page React Router routes are implemented. `createBrowserRouter([{ path: "*", element: <App /> }])` is the only route.

## Components

- Page components: `frontend/src/routes/App.tsx`.
- Shared API client: `frontend/src/shared/api/client.ts`.
- Test setup: `frontend/src/test/setup.ts`.
- Dedicated shared UI/form/error/loading components: NOT IMPLEMENTED.
- Route guards: NOT IMPLEMENTED; role-based query `enabled` conditions exist in `App.tsx`.

## State Management

- React Query: all API reads and mutations.
- Local state: selected local user, selected assignment, last submission/review/runner/exam statuses.
- Persisted auth state: `localStorage` key `taiga.localUser`.
- URL state: NOT IMPLEMENTED.
- Context: only QueryClient provider.

## API Usage

| API function | Query/mutation | Role condition | Notes |
|---|---|---|---|
| `getHealth` | query `health` | anonymous | Hits `/health` outside `/api/v1` |
| `getMe` | query `me` | selected local user | Uses local bearer token |
| `getReviewQueue` | query | reviewer/admin only | Avoids expected 403 console noise |
| Admin queries | query | admin only | Users, feature flags, analytics, curriculum |
| `createDemoSubmission` | mutation | signed-in learner path in UI | Creates upload, completes upload, submits assignment |
| `reviewSubmission` | mutation | reviewer/admin UI enabled | Uses first pending review |
| Exam flow mutations | mutation | disabled by default in UI | Button disabled when `exam_enabled=false` |

## Gaps

| ID | Gap | Evidence | Target phase |
|---|---|---|---|
| FE-001 | No dedicated pages for curriculum, assignment detail, review queue, admin management, exam | Single wildcard route | Phase 6 |
| FE-002 | Error states are mostly implicit and not user-specific | `App.tsx` uses fallback counts/text | Phase 6 |
| FE-003 | Loading states are minimal | No skeleton/spinner components | Phase 6 |
| FE-004 | Forms use direct button actions; React Hook Form is installed but not used | `package.json`, `App.tsx` | Phase 6 |
| FE-005 | No accessibility tooling such as axe | Dependencies and tests | Phase 6 |

