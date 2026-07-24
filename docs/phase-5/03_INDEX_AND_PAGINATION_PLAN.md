# Index and Pagination Plan

## Index Decisions

| Table | Columns | Query supported | Before plan | After plan | Write cost | Decision |
|---|---|---|---|---|---|---|
| `outbox_events` | `event_type,next_attempt_at,created_at` where `published_at IS NULL` | Worker claim for due runner jobs | Seq scan over unpublished outbox rows | Index scan using `outbox_unpublished_type_due_idx` | One additional partial index entry for unpublished outbox writes | Added |
| `submissions` | Review queue candidate | Reviewer queue | Seq scan over 37 local rows | Not proven beneficial on seed data | Extra write cost on submissions | Not added |
| `task_assignments` | Existing `learner_id,status,scheduled_date` | Learner list/status filters | Existing index available | No new index needed | None | Kept existing |
| `users` | Existing unique `cognito_sub` | Local auth lookup | Existing unique index available | No new index needed | None | Kept existing |

## Migration

- Migration ID: `0002_phase5_performance_indexes`
- Upgrade: creates `outbox_unpublished_type_due_idx`
- Rollback: drops `outbox_unpublished_type_due_idx`
- Data migration: none
- Lock risk: low locally; production should schedule index creation carefully or use concurrent creation in a production-specific migration strategy.

## Pagination and Limits

Growing list endpoints now validate `limit` with `ge=1` and `le=100`:

- `/api/v1/assignments`
- `/api/v1/reviews/queue`
- `/api/v1/exams`
- `/api/v1/notifications`
- `/api/v1/admin/users`
- `/api/v1/admin/curriculum/versions`

Current paging remains bounded first-page pagination with stable ordering and `nextCursor=null`. Cursor pagination is deferred until datasets exceed Local MVP scale or API contract work requires it.

## Regression Tests

`test_list_limits_are_bounded` verifies `limit=0` and `limit=101` are rejected and `limit=100` succeeds for representative list endpoints.
