# Observability Baseline

| Capability | Status | Evidence |
|---|---|---|
| Backend access logs | Implemented by Uvicorn default | Docker logs show request lines |
| Backend structured logs | NOT IMPLEMENTED | No logging config |
| Worker logs | Minimal | `worker.py` startup and DB retry prints |
| Runner logs | Minimal | `runner_controller.py` startup print |
| Health endpoint | Implemented | `/health`, `/api/v1/health/live` |
| Readiness endpoint | Implemented | `/ready`, `/api/v1/health/ready` |
| Metrics | NOT IMPLEMENTED | No metrics dependency |
| Tracing | NOT IMPLEMENTED | No tracing dependency |
| Correlation ID | NOT IMPLEMENTED | No middleware |
| Audit events | Partially implemented | `audit_events` table; submission create writes one event |
| Sensitive data masking | UNKNOWN | No central logging/masking policy in code |
| Alerting | NOT IMPLEMENTED | No operations integration |
| Retention | NOT IMPLEMENTED | No log retention config |

Target phases: Phase 4 for sensitive logging, Phase 7 for production observability.

