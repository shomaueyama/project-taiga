# Route and Navigation Map

## Routes

| Route | Role visibility | Behavior |
|---|---|---|
| `/` | learner, reviewer, admin | Resolves to dashboard content |
| `/dashboard` | learner, reviewer, admin | Learning metrics and current state |
| `/assignments` | learner, admin | Assignment list, selected assignment, demo submission |
| `/assignments/:assignmentId` | learner, admin | Direct assignment detail lookup |
| `/reviews` | reviewer, admin | Review queue and review actions |
| `/runner` | learner, admin | Runner status and last-submission run action |
| `/exams` | learner, admin | Exam status and guarded start action |
| `/admin` | admin | Users, analytics, curriculum, feature flags |
| unknown route | all | Japanese not-found state with dashboard link |

## Navigation Behavior

- Browser back/forward works through React Router links.
- Direct assignment routes refresh safely because the route id is parsed from the URL.
- Role-specific navigation is only a UX aid; backend authorization remains authoritative.
- Active navigation uses `aria-current="page"` and a left indicator, not color alone.
- Route changes move focus to `#main-content`.
- Unauthorized direct routes show safe explanatory text and avoid privileged data queries where
  possible.

## Deferred

- Dedicated `/submissions/:submissionId`, `/reviews/:submissionId`, and `/exams/:attemptId` routes
  are deferred until the UI has richer detail screens.
