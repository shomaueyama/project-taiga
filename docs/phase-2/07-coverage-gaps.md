# Coverage Gaps

Initial gaps:

- Backend admin and assignment query modules are below target.
- Backend validation and worker modules have little direct coverage.
- Frontend App action handlers and API client branches are undercovered.
- E2E does not yet cover enabled Exam/Runner paths at browser level.

## Final Gaps and Exceptions

- `worker.py` remains at 0% direct unit coverage. Its behavior is indirectly covered through
  runner job integration tests; deeper worker claim/retry tests are deferred to runner hardening.
- `validation.py` remains at 77%. Phase 2 covers success entrypoints; negative schema fixture
  coverage is deferred until the validation contract stabilizes further.
- Docker browser E2E stays on default disabled `RUNNER_ENABLED=false` and `EXAM_ENABLED=false`.
  Enabled paths are covered in backend integration and frontend component tests to avoid feature
  flag restarts inside the parallel E2E suite.
