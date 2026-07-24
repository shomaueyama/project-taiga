# Load Test Plan and Results

## Tool

`scripts/perf_load.py` uses Python standard library HTTP requests and `ThreadPoolExecutor`. It is local-only and targets read paths.

## Scenarios

| Scenario | Requests | Concurrency | Paths |
|---|---:|---:|---|
| smoke | 40 | 2 | health, dashboard, assignments, progress, review queue |
| baseline | 200 | 8 | health, dashboard, assignments, progress, review queue |
| stress | 500 | 20 | health, dashboard, assignments, progress, review queue |

Review queue requests use `reviewer@example.local`; other API requests use `taiga@example.local`.

## Results

| Scenario | Requests | Concurrency | Duration s | p50 ms | p95 ms | p99 ms | Throughput rps | Error rate | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| baseline | 200 | 8 | 0.491 | 18.63 | 38.41 | 66.03 | 407.71 | 0.0 | 200 only |
| stress | 500 | 20 | 0.497 | 8.70 | 54.98 | 79.68 | 1006.62 | 0.0 | 228x 200, 272x 429 |

The stress scenario intentionally exceeds the local rate limit. HTTP 429 responses were expected and are not counted as 5xx errors.

## Reproduce

```bash
python3 scripts/perf_load.py --scenario smoke
python3 scripts/perf_load.py --scenario baseline
python3 scripts/perf_load.py --scenario stress
```
