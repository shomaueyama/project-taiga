# Performance Budgets

Budgets are local MVP budgets based on Phase 5 measurements.

## API

- Common read endpoint p95 should remain below 75ms under baseline local load.
- Baseline read-path load should have 0% HTTP 5xx.
- List endpoint response bodies should remain below 10KB for default page size.
- List `limit` must stay between 1 and 100.

## Database

- Representative read endpoints should remain at or below current query counts unless justified:
  - `/me`: 1
  - `/dashboard`: 3
  - `/assignments`: 2
  - `/progress`: 4
  - `/exams`: 2
- Worker claim must use an index when unpublished outbox rows are present.
- No confirmed N+1 is allowed on first-screen Local MVP routes.

## Worker

- Idle poll default: 5 seconds.
- Error retry default: 30 seconds.
- Poison messages must not block later healthy jobs.
- 10 local runner jobs should process in under 1 second with runner execution disabled.

## Frontend

- Initial JS gzip budget: 150KB.
- CSS gzip budget: 5KB.
- Production build should complete in under 10 seconds locally.
- Existing 6 Playwright flows must continue to pass.
