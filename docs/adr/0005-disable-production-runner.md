# ADR 0005: Disable Production Runner

Production sets `RUNNER_ENABLED=false`.

The local runner is intentionally isolated for the MVP, but AWS production runner
execution needs a separate security design before it can process learner code.

