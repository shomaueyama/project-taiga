# Application Runtime

Backend and worker run as ECS Fargate services.

Production runtime guardrails:

- `APP_ENV=production`
- `LOCAL_AUTH_ENABLED=false`
- `RUNNER_ENABLED=false`
- `EXAM_ENABLED=true`
- Worker has no load balancer and no public ingress.

Images must be deployed by immutable digest from ECR.

