# Local MVP Test Matrix

This matrix defines 100% coverage for the currently implemented Local MVP surface. Full multi-page
assignment, exam, and admin management screens are not implemented yet; their API contracts are
covered by backend tests and the single-page frontend exposes their local status.

| ID | Feature | Happy Path | Error/Auth/Boundary | Test |
| --- | --- | --- | --- | --- |
| LMVP-AUTH-001 | Local learner identity | Learner resolves as 上山 虎雅 | Unknown local user shows no page crash | `local-mvp.spec.ts` |
| LMVP-AUTH-002 | Local admin identity | Admin resolves as 上山 捷馬 | Learner cannot use admin queries | `local-mvp.spec.ts` |
| LMVP-SEED-001 | Canonical curriculum seed | 28 weeks, 196 tasks, 28 exams, 56 variants | Seed can run twice without duplicates | `test_local_demo_seed_integration.py` |
| LMVP-SEED-002 | Realistic local fixtures | Assignments, submissions, reviews, runner, exam states | Local-only guard | `test_local_demo_seed_integration.py` |
| LMVP-DASH-001 | Dashboard | Today, progress, next exam, rank render | Empty values render as `none`/`not ranked` | `App.test.tsx`, `local-mvp.spec.ts` |
| LMVP-ASG-001 | Assignments | Assignment list and detail render | Missing detail handled by query failure state | `App.test.tsx`, `local-mvp.spec.ts` |
| LMVP-SUB-001 | Submission | Demo submission creates upload and immutable submission | Upload validation rejects traversal/extensions | `test_upload_security.py`, `local-mvp.spec.ts` |
| LMVP-REV-001 | Review queue | Admin sees queue and can approve pending item | Learner review controls disabled | `local-mvp.spec.ts` |
| LMVP-RUN-001 | Runner disabled state | Disabled state renders safely | Run button disabled; no HTTP 500 | `local-mvp.spec.ts`, `test_runner_jobs.py` |
| LMVP-EXAM-001 | Exam disabled state | Scheduled exams render | Start disabled; no HTTP 500 | `local-mvp.spec.ts`, `test_exam.py` |
| LMVP-ADMIN-001 | Admin operations | Users, analytics, curriculum, feature flags render | Learner sees admin restriction | `local-mvp.spec.ts` |
| LMVP-QA-001 | Browser runtime quality | No `pageerror`, `console.error`, request failure, or HTTP 5xx | Repeat run checks flake risk | `npx playwright test --repeat-each=3` |

## Coverage Scope

Backend unit and integration coverage includes local auth, upload validation, curriculum seed,
realistic seed idempotency, runner sanitization, and exam oral review schema. Migration files and
generated package metadata are excluded from coverage expectations because they are validated by
Alembic migration execution and packaging checks instead of line coverage.

Frontend coverage includes the implemented single-page Local MVP shell, login selector, dashboard,
assignment detail, submission action, disabled runner/exam states, review action, and admin summary.
Generated Vite entry code and type-only declarations are not counted as feature behavior.
