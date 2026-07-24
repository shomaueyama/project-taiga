# Cost And Limits

Status: values below are based on Cloudflare official documentation checked on 2026-07-24. The owner
must verify limits again before deployment.

## Confirmed Repository Facts

- Frontend is static React/Vite and suitable for edge static delivery.
- Backend is Python/FastAPI and not directly runnable as a Cloudflare Worker.
- Database is PostgreSQL-specific.
- Runner is disabled and must remain disabled in production.

## Confirmed Platform Facts

Sources:

- Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- D1 limits: https://developers.cloudflare.com/d1/platform/limits/
- D1 pricing: https://developers.cloudflare.com/d1/platform/pricing/
- R2 pricing: https://developers.cloudflare.com/r2/pricing/
- R2 limits: https://developers.cloudflare.com/r2/platform/limits/
- Queues limits: https://developers.cloudflare.com/queues/platform/limits/
- Queues pricing: https://developers.cloudflare.com/queues/platform/pricing/
- Pages limits: https://developers.cloudflare.com/pages/platform/limits/

Confirmed summary:

- Workers Free: 100,000 requests/day and 10 ms CPU time per invocation.
- Workers paid Standard includes higher monthly request/CPU allocation and paid overages.
- D1 Free: smaller database/account limits than paid; official docs list 500 MB maximum database size
  on Free and 10 GB on Workers Paid.
- D1 Free has lower per-invocation query subrequest limits than paid.
- R2 Free tier includes 10 GB-month storage, 1 million Class A operations/month, and 10 million Class
  B operations/month for Standard storage.
- Queues are available on Workers Free, but operation limits and consumer wall-time limits apply.
- Queue consumers and Cron Triggers have 15-minute wall-time limits.
- Pages Free has static site file-count limits.

## Assumptions

- TAIGA NOVA initial public usage is small.
- Uploaded learner artifacts stay below current 50 MB application limit.
- Runner execution remains disabled.
- No heavy search, analytics, AI, or media processing is required in the initial Cloudflare release.

## Estimates

| Usage model | Likely bottleneck | Notes |
|---|---|---|
| 10 active users | D1 migration effort, not platform limits | Free tier likely enough if uploads are modest. |
| 100 active users | D1 reads/writes, R2 operations, Workers CPU | Need query counting and cache strategy before production. |
| 1,000 active users | D1 size/concurrency, Queue operations, observability | Upgrade trigger likely; consider PostgreSQL/AWS path or paid Cloudflare plan. |

## Likely Free-Plan Bottlenecks

- D1 database size and daily query limits.
- Workers 10 ms CPU limit if API route logic remains heavy.
- Upload storage and object operation volume.
- Queue operation limits if every submission produces multiple async messages.
- Observability/log retention depth.

## Upgrade Triggers

- D1 database approaches free storage limit.
- Daily D1 read/write limits are hit.
- Worker CPU routinely exceeds free CPU budget.
- R2 storage or operations exceed free tier.
- Need stronger logs, retention, or security controls.

## Items Requiring Owner Verification

- Exact Cloudflare plan selected.
- Whether R2 subscription setup is required for the account.
- Current Cloudflare billing currency and tax handling.
- Custom domain/DNS ownership.
- Whether private GitHub repository integration is allowed.

