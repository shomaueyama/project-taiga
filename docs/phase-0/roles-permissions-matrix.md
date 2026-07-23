# Roles and Permissions Matrix

## Implemented Roles

DB enum `user_role`: `learner`, `reviewer`, `admin`.

Evidence: `backend/alembic/versions/0001_initial_schema.py`, `auth.py`, seed users.

## Matrix

| Action | Anonymous | Learner | Reviewer | Admin | Enforcement location | Test coverage |
|---|---|---|---|---|---|---|
| login/local identity | No | Yes | Yes | Yes | `auth.py` | backend/e2e |
| logout | N/A | localStorage selector only | localStorage selector only | localStorage selector only | Frontend only | E2E implicit |
| system health read | Yes | Yes | Yes | Yes | `/health` no auth | health test |
| dashboard read | No | Own principal | reviewer gets own scoped empty/limited view | admin gets own scoped view | `get_current_principal`; query uses principal id | E2E |
| assignment read | No | Own assignments | Own assignments only | Own assignments only | `assignment_queries.py` | E2E partial |
| submission create | No | Own assignment | only if assigned to reviewer | only if assigned to admin | `create_submission` checks learner_id=principal.id | E2E learner |
| review queue read | No | No | Yes | Yes | `review_queue` role check | E2E admin |
| review approve/reject | No | No | Yes | Yes | `create_review` role check | E2E admin |
| user management | No | No | No | Yes | `require_admin` | E2E admin display |
| curriculum versions read | No | No | No | Yes | `require_admin` | E2E admin |
| feature flag update | No | No | No | Yes | `require_admin` | Not covered |
| exam start | No | Yes if attempt belongs to principal | Reviewer can access attempts via reviewer path but start behavior needs review | Admin can access attempts via reviewer path but start behavior needs review | `exam_service._attempt_row` | partial unit |
| runner execute | No | Own submission | reviewer/admin can access submission | reviewer/admin can access submission | `get_submission_summary` | runner unit |

UNKNOWN: Whether reviewer/admin should be allowed to start learner exam attempts is not specified by implementation tests.

