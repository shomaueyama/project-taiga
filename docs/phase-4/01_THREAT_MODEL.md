# Threat Model

## Assets

User identity, role information, assignments, submissions, upload records, reviews, exam attempts, runner requests, runner results, curriculum seed data, PostgreSQL contents, local configuration, logs, and outbox messages.

## Actors

Unauthenticated attacker, learner, reviewer, admin, compromised account, malicious uploaded content, malicious runner payload, compromised dependency, and accidental local operator misconfiguration.

## Entry Points

Frontend routes, local authentication headers, API path and query parameters, JSON request bodies, upload metadata, submission and review mutations, exam mutations, runner queue requests, worker outbox processing, Docker Compose service boundaries, environment configuration, and logs.

## Threats and Mitigations

| Threat | Relevant Surface | Mitigation | Residual Risk |
|---|---|---|---|
| Spoofing | LocalAuth headers | LocalAuth is restricted to `APP_ENV=local`; unknown or inactive users fail. | Local mode intentionally trusts local bearer/header identity. |
| Tampering | Request bodies | Strict Pydantic models reject unknown fields and constrain lengths, counts, and ranges. | Duplicate JSON keys are still parsed by the JSON decoder behavior. |
| Repudiation | Mutations and worker messages | Idempotency headers are required on active mutations; audit/outbox tables exist in the schema. | Audit coverage is not yet comprehensive for every mutation. |
| Information disclosure | Errors, browser responses | App errors map to stable codes; security headers and no-store cache headers are added. | Framework validation payloads can reveal field names by design. |
| Denial of service | API and health endpoints | Local in-memory rate limiting is enabled by default. | Rate limits are process-local and not distributed. |
| Elevation of privilege | Review and admin APIs | Shared authorization policies enforce reviewer/admin roles. | Reviewer scoping remains intentionally narrow in Local MVP. |
| IDOR | Resource IDs | Service queries scope learner resources by principal and return 404 for unrelated resources. | More nested mismatch tests are deferred for inactive endpoints. |
| Mass assignment | JSON models | Request schemas forbid extra fields. | Read-only response models still include expected public fields. |
| Injection | Runner requests | Unsafe metacharacters and control characters are rejected before queue creation. | Full untrusted code execution remains disabled by default. |
| Path traversal | Upload metadata | Absolute paths, separators, `..`, `~`, and Windows drive markers are rejected. | File content scanning is not implemented. |
| SSRF | URLs | Repository URLs are length-bounded and are not fetched by the API. | Future integrations must validate network egress. |
| Feature-flag bypass | Runner and exam | Boolean flags fail closed unless explicitly `true` or `false`. | Runtime flag persistence is still local and admin-controlled. |
| Secret leakage | Containers and logs | Docker socket mounts were removed; no production secrets are required. | Local Compose includes a non-secret development database password. |

## Security Boundary

The Local MVP security boundary is the backend API and PostgreSQL database. The frontend is not trusted for authorization, state transitions, deadlines, upload safety, or runner execution safety.
