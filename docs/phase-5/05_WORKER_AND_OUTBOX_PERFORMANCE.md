# Worker and Outbox Performance

## Baseline

Before Phase 5, worker idle polling slept for 30 seconds. This avoided tight polling but made worst-case queue delay too high for local feedback.

The outbox claim query filtered by `event_type` after using only the existing unpublished index, and the seed plan showed a sequential scan over 41 outbox rows.

## Changes

- Added `WORKER_IDLE_POLL_SECONDS`, default `5`.
- Added `WORKER_ERROR_RETRY_SECONDS`, default `30`.
- Added `outbox_unpublished_type_due_idx` for due unpublished events by type.
- Preserved single-job claim semantics with `FOR UPDATE SKIP LOCKED`.
- Preserved `attempt_count`, poison handling, and idempotent processing.

## Measurements

Synthetic safe local runner-job processing:

| Jobs | Total seconds | Jobs/sec | Avg ms/job |
|---:|---:|---:|---:|
| 10 | 0.0567 | 176.46 | 5.67 |

Load used DB-inserted runner jobs and `process_next_runner_job`; hostile code execution remained disabled.

## Poison Message Behavior

Regression coverage verifies that a poison runner outbox event is delayed and does not block a later healthy runner job.

## Trade-Offs

Reducing idle sleep from 30s to 5s increases idle polling from about 2 queries/minute to about 12 queries/minute per worker. This is acceptable for Local MVP responsiveness and is configurable for production-like environments.
