# CI/CD

Phase 7 CI adds:

- Terraform formatting validation.
- Terraform init with `-backend=false`.
- Terraform validate for staging and production.
- Docker Compose image build validation.

Terraform plan/apply with AWS credentials remains outside pull request CI until GitHub
environments, OIDC roles, and approval gates are configured.

