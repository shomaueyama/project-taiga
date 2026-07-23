# Risk-Based Test Matrix

| Role | Feature | State/transition | Positive | Negative | Duplicate/idempotent | Stale/concurrent | Layer | Current coverage | Final coverage |
|---|---|---|---|---|---|---|---|---|---|
| anonymous | auth | unauthenticated | N/A | `/me` 401 | N/A | N/A | backend/E2E | covered | Covered |
| learner | auth | local session | known local user allowed | unknown rejected | localStorage selection | env leakage | backend/frontend | partial | Covered |
| learner | assignment | owned assignment detail | own assignment visible | other learner/missing assignment denied | N/A | status drift | backend | partial | Covered |
| learner | submission | first submission | accepted upload creates vN | invalid upload rejected | same operation does not corrupt versions | concurrent submissions serialized | backend/E2E | partial | Covered |
| reviewer/admin | review | pending to approved | approve pending | learner rejected | double approve rejected | simultaneous review attempts | backend/E2E | partial | Covered |
| reviewer/admin | review | pending to needs_revision | reject pending | already approved/rejected rejected | double reject rejected | simultaneous review attempts | backend/E2E | partial | Covered |
| admin | admin ops | user/flag operations | list/invite/suspend/restore/update flag | learner/reviewer rejected | repeated invite safe | stale feature flag version | backend/frontend | partial | Covered |
| learner/reviewer/admin | exam disabled | mutation blocked | safe 403 | no mutation side effect | duplicate blocked | N/A | backend/frontend/E2E | partial | Covered |
| learner/admin | exam enabled | ready to passed/failed/expired | reserve/start/submit/oral | invalid order rejected/safe | duplicate start/submit safe | ownership checks | backend/frontend | partial | Covered below browser E2E |
| learner/admin | runner disabled | queue blocked | safe 403 | no job queued | duplicate blocked | N/A | backend/frontend/E2E | partial | Covered |
| learner/admin | runner enabled local | queued to security_rejected | safe rejection redacts hidden tests | unauthorized rejected | repeated processing safe | duplicate processing | backend/frontend | partial | Covered below browser E2E |
| system | seed/migration | clean and repeated setup | migrate/seed twice | missing design pack skipped explicitly | seed idempotent | restart persistence | backend/Docker | partial | Covered |
| frontend | UI states | loading/empty/error/success | user-visible states render | API failure visible | duplicate action guarded | query cache isolation | frontend | weak | Covered |
| e2e | critical flow | learner/reviewer/admin | deterministic role flows | unauthorized/disabled flows | duplicate review protected | no queue order dependence | E2E | partial | Covered for Phase 1 enabled surface |
