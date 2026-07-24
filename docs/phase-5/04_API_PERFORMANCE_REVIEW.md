# API Performance Review

## Response Sizes

Representative response sizes:

| Endpoint | Bytes |
|---|---:|
| `/health` | 77 |
| `/api/v1/dashboard` | 726 |
| `/api/v1/assignments` | 3191 |
| `/api/v1/progress` | 223 |
| `/api/v1/exams` | 3250 |

## Findings

- List endpoints are bounded and now reject unreasonable limits.
- Assignment and exam list payloads are modest in seeded local data.
- Dashboard response is compact and avoids returning all assignments.
- No large nested response was found in the first-screen Local MVP flow.
- API response contracts remain aligned with the existing frontend and OpenAPI shape.

## Changes

- Added explicit FastAPI query validation for list limits.
- Kept response shapes unchanged.

## Caching Decision

No server-side cache was added. Current query counts and latencies do not justify cache invalidation complexity, and several responses are user-scoped or stateful.
