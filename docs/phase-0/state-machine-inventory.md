# State Machine Inventory

## Assignment

Statuses: `not_started`, `available`, `in_progress`, `awaiting_submission`, `completed`, `missed`, `cancelled`.

```mermaid
stateDiagram-v2
  [*] --> not_started
  not_started --> available: seed/schedule
  available --> in_progress: learner starts (UNKNOWN API)
  in_progress --> awaiting_submission: ready to submit (UNKNOWN API)
  awaiting_submission --> completed: approved/reconciled (UNKNOWN)
  available --> missed: due date policy (UNKNOWN implementation)
  not_started --> cancelled
```

Evidence: DB enum and seed. Transition enforcement is mostly UNKNOWN.

## Submission

Statuses: `draft`, `submitted`, `queued`, `running`, `automated_passed`, `automated_failed`, `manual_review_pending`, `needs_revision`, `approved`, `cancelled`.

```mermaid
stateDiagram-v2
  [*] --> manual_review_pending: create_submission
  manual_review_pending --> approved: review approved
  manual_review_pending --> needs_revision: review needs_revision
  needs_revision --> manual_review_pending: resubmission creates new version
  manual_review_pending --> queued: run request
  queued --> manual_review_pending: runner disabled local success
  queued --> needs_revision: security_rejected
```

Evidence: `submission_service.py`, `runner_jobs.py`.

## Runner Job

Statuses: `queued`, `claimed`, `preflight`, `building`, `public_testing`, `hidden_testing`, `sanitizing`, `succeeded`, `failed`, `timed_out`, `cancelled`, `security_rejected`.

```mermaid
stateDiagram-v2
  [*] --> queued
  queued --> succeeded: local disabled worker
  queued --> security_rejected: runner_enabled true placeholder
```

Most contract transitions are not implemented.

## Exam Attempt

Statuses: `scheduled`, `ready`, `in_progress`, `submitted`, `evaluating`, `oral_pending`, `passed`, `failed`, `expired`, `cancelled`.

```mermaid
stateDiagram-v2
  [*] --> ready: reserve_attempt
  ready --> in_progress: start_attempt
  in_progress --> oral_pending: submit before deadline
  in_progress --> expired: late submit
  oral_pending --> passed: oral review passed
  oral_pending --> failed: oral review failed
```

`scheduled`, `submitted`, `evaluating`, `cancelled` are enum values but not actively transitioned by current services.

## Outbox

`outbox_events` has `published_at`, `attempt_count`, `next_attempt_at`, `last_error`.

```mermaid
stateDiagram-v2
  [*] --> unpublished: insert row
  unpublished --> published: worker sets published_at
  unpublished --> unpublished: retry not fully implemented
```

