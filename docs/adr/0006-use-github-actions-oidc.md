# ADR 0006: Use GitHub Actions OIDC

GitHub Actions should authenticate to AWS through OIDC instead of long-lived AWS keys.

The initial Terraform module creates an environment-scoped deploy role skeleton. Its
permissions must be expanded deliberately during the approved deployment phase.

