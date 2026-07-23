# Domain Model and Invariants

## Model

- User: authenticated local actor with role, status, timezone, and display name.
- Role: `learner`, `reviewer`, or `admin`.
- Curriculum / Week / Task Template: canonical seed data from the read-only design pack.
- Assignment: learner-owned task instance with schedule and progress status.
- Submission: immutable learner work record for one assignment.
- Submission Version: monotonically increasing per assignment.
- Review: reviewer/admin decision on a `manual_review_pending` submission.
- Exam: scheduled assessment with active variants.
- Exam Variant / Attempt: learner attempt reserves one unseen variant snapshot.
- Runner Request / Job: optional execution request gated by `RUNNER_ENABLED`.
- Outbox / Worker Event: transactional outbox row consumed by the local worker.

## Invariants

- Unknown local users receive 401.
- Inactive users receive 403.
- Admin-only operations require `admin`.
- Review operations require `reviewer` or `admin`.
- Learners may only access their own assignments, uploads, submissions, and exam attempts.
- Reviewers/admins may access review and exam review surfaces as explicitly allowed.
- A submission can be reviewed only from `manual_review_pending`.
- A reviewed submission cannot be reviewed again.
- Review approval sets submission to `approved` and assignment to `completed`.
- Review needs-revision sets submission to `needs_revision` and assignment to `in_progress`.
- Submission versions are allocated under a locked assignment row.
- Runner mutation requires `RUNNER_ENABLED=true`; disabled requests fail with no queued job.
- Exam mutation requires `EXAM_ENABLED=true`; disabled requests fail with no attempt mutation.
- Hidden runner result data remains redacted in learner-visible responses.
- Oral review can pass/fail only an `oral_pending` exam attempt.
- Transaction rollback must prevent partial side effects after invalid transitions.
