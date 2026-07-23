# State Transition Map

| Entity | Current state | Action | Actor | Preconditions | Next state | Side effects | Failure status | Transaction / lock |
|---|---|---|---|---|---|---|---|---|
| Assignment | available/in_progress/etc | create submission | learner owner | accepted upload IDs belong to learner | unchanged | submission vN, artifacts, outbox, audit | 404/409 | assignment row `FOR UPDATE` |
| Submission | none | create submission | learner owner | assignment exists and uploads accepted | manual_review_pending | immutable version allocated | 404/409 | assignment row `FOR UPDATE` |
| Submission | manual_review_pending | approve | reviewer/admin | submission exists | approved | review row, notification, assignment completed | 403/404/409 | submission row `FOR UPDATE` |
| Submission | manual_review_pending | needs revision | reviewer/admin | submission exists | needs_revision | review row, notification, assignment in_progress | 403/404/409 | submission row `FOR UPDATE` |
| Submission | approved/needs_revision | review again | reviewer/admin | none | unchanged | none | 409 | submission row `FOR UPDATE` |
| Runner job | none | request run | learner/reviewer/admin allowed by submission access | `RUNNER_ENABLED=true` | queued | runner job row, outbox, submission queued | 403/404 | request transaction |
| Runner job | queued | worker process, runner disabled | worker | outbox event unpublished | succeeded | sanitized disabled result, submission manual_review_pending | none | outbox `FOR UPDATE SKIP LOCKED` |
| Runner job | queued | worker process, runner enabled placeholder | worker | outbox event unpublished | security_rejected | sanitized redacted result, submission needs_revision | none | outbox `FOR UPDATE SKIP LOCKED` |
| Exam attempt | none | reserve attempt | learner | `EXAM_ENABLED=true`, unseen variant exists | ready | attempt row with variant snapshot | 403/409 | variant row `FOR UPDATE` |
| Exam attempt | ready | start | learner owner | rules acknowledged | in_progress | server start/deadline timestamps | 403/409 | request transaction |
| Exam attempt | in_progress | submit before deadline | learner owner | server deadline not passed | oral_pending | result snapshot and submitted_at | 403/404 | request transaction |
| Exam attempt | in_progress | submit after deadline | learner owner | server deadline passed | expired | no answer acceptance | 403/404 | request transaction |
| Exam attempt | ready/oral_pending/etc | submit invalid order | learner owner | not in_progress | unchanged | none | 200 existing behavior | request transaction |
| Exam attempt | oral_pending | oral pass | reviewer/admin | `EXAM_ENABLED=true` | passed | oral result, rank history | 403/404/409 | request transaction |
| Exam attempt | oral_pending | oral fail | reviewer/admin | `EXAM_ENABLED=true` | failed | oral result | 403/404/409 | request transaction |
| Exam attempt | ready/passed/failed/etc | oral review invalid order | reviewer/admin | not oral_pending | unchanged | none | 409 | rollback verified |

Pure transition decisions live in `taiga.state_transitions`.
