# Feature Flag Inventory

| Flag | Default | Env source | Backend use | Frontend use | Disabled behavior | Test |
|---|---|---|---|---|---|---|
| `LOCAL_AUTH_ENABLED` | true | `.env.example`, `Settings` | Required for local auth; fail-fast outside local | Not directly | 401 when false | auth tests |
| `RUNNER_ENABLED` | false | `.env.example`, Compose | `runner_jobs.py` chooses disabled local result; runner-controller logs flag | `/health.runner_enabled` disables run button | No learner code execution; sanitized text | E2E |
| `EXAM_ENABLED` | false | `.env.example`, Compose | Reported in health; exam APIs still callable if directly used | `/health.exam_enabled` disables start button | UI prevents start; API does not enforce flag | E2E UI |
| `runner.enabled` | false | DB seed `feature_flags` | Admin list/update only | Admin feature flag list | Display only | E2E admin display |
| `exam.enabled` | false | DB seed `feature_flags` | Admin list/update only | Admin feature flag list | Display only | E2E admin display |

## Gaps

- Env flags and DB flags are separate; no unified provider is implemented.
- `EXAM_ENABLED=false` does not appear to block direct backend exam APIs.
- AWS adapter flags are NOT IMPLEMENTED.

