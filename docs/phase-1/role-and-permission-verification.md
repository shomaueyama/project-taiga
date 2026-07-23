# Role and Permission Verification

| Operation | Anonymous | Learner | Reviewer | Admin |
|---|---|---|---|---|
| `/api/v1/me` | 401 | own profile | own profile | own profile |
| Learner dashboard | 401 | allowed | scoped to own user | scoped to own user |
| Assignment detail | 401 | own assignment only | own assignment only | own assignment only |
| Review queue | 401 | 403 | allowed | allowed |
| Review decision | 401 | 403 | allowed for pending submissions | allowed for pending submissions |
| Admin users | 401 | 403 | 403 | allowed |
| Runner queue | 401 | safe disabled response | safe disabled response | safe disabled response |
| Exam mutation | 401 | safe disabled response | safe disabled response | safe disabled response |

## Phase 1 Evidence

- Anonymous `/api/v1/me`: PASS, `401`.
- Unknown local user: PASS, `401`.
- Known local users: PASS for learner, reviewer, and admin.
- Learner admin access: PASS, `403`.
- Admin user list: PASS.
- Review duplicate/immutable state: PASS, already-approved submissions return `409`.
- Cross-test direct object conflicts: submission version allocation now uses row locking.
