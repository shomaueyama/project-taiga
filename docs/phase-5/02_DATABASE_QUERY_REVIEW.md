# Database Query Review

## Representative Query Counts

| Endpoint | Query Count | Finding |
|---|---:|---|
| `/api/v1/me` | 1 | No N+1. |
| `/api/v1/dashboard` | 3 | Bounded and predictable. |
| `/api/v1/assignments?limit=20` | 2 | Bounded and predictable. |
| `/api/v1/progress` | 4 | Multiple aggregate lookups, acceptable for local MVP. |
| `/api/v1/exams` | 2 | Bounded and predictable. |

## Query Plans Reviewed

### Assignments List

Seeded local data uses sequential scans over 196 assignments and 196 templates. Execution time was 3.453ms. Existing unique and learner/status/date indexes are adequate for current scale.

### Review Queue

The seeded review queue query used a sequential scan over 37 submissions and completed in 0.107ms. A proposed review queue index was not kept because the seeded plan did not prove value.

### Outbox Claim

Before Phase 5, the worker claim query scanned `outbox_events` and filtered by `event_type`.

After Phase 5:

```text
Index Scan using outbox_unpublished_type_due_idx on outbox_events
Index Cond: event_type = 'runner_job.queued' AND next_attempt_at <= now()
Execution Time: 0.065 ms
```

This index is justified because outbox rows can grow across event types and poison/retry rows should not force scans over unrelated unpublished messages.

## N+1 Review

No confirmed N+1 issue was found in the representative endpoints. The backend currently uses explicit SQL and bounded result sets rather than ORM lazy loading.
