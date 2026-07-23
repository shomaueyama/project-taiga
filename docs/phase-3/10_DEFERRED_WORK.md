# Deferred Work

| Area | Deferred item |
|---|---|
| Backend routes | Split `main.py` into feature routers after more endpoints are implemented |
| Persistence | Consider focused repositories only where SQL duplication becomes costly |
| Error model | Convert remaining legacy built-in service exceptions and native FastAPI errors to a broader catalog |
| OpenAPI | Implement or explicitly stub AI usage, notification mutation, and curriculum import endpoints |
| Frontend | Add shared status label/error classification modules when UI grows beyond the Local MVP shell |
| Worker | Add direct worker claim/retry unit tests during runner hardening |
| Runner | Implement isolated disposable runner and hostile fixture suite in the runner phase |
| Exam | Add browser E2E for enabled exam flow under an isolated feature-flag stack |
