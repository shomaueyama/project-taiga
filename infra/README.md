# Project Taiga Production Infrastructure

This directory contains the Phase 7 Terraform foundation for Project Taiga.

It is intentionally deployment-ready but not auto-deploying. Do not run `terraform apply`
until AWS account ownership, Route53/ACM inputs, remote state, GitHub environments, and
production rollout approval are confirmed.

## Environments

- `environments/staging`
- `environments/production`

Both environments use the shared modules under `infra/modules`.

## Local Validation

```bash
make terraform-fmt
make terraform-validate
```

Terraform validation requires the Terraform CLI. The validation target initializes each
environment with `-backend=false`; it does not create AWS resources.

## Deployment Guard

`infra/scripts/apply.sh` refuses to run unless:

```bash
ALLOW_TAIGA_TERRAFORM_APPLY=yes infra/scripts/apply.sh staging
```

This guard is deliberate. Phase 7 in this repository records the infrastructure plan and
validation path; actual AWS resource creation requires owner approval.

