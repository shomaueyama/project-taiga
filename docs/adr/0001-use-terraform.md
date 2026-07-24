# ADR 0001: Use Terraform

Project Taiga uses Terraform for production infrastructure because it provides explicit
state, reusable modules, and mature AWS provider support.

Alternatives considered: CDK and manual AWS console setup.

Decision: keep production infrastructure under `infra/` with environment-specific roots.

