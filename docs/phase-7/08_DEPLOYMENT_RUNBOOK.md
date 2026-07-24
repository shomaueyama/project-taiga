# Deployment Runbook

Deployment is intentionally gated.

Preparation:

1. Confirm AWS account and region.
2. Create or identify remote state bucket and lock table.
3. Replace `backend.tf` placeholders.
4. Configure ACM certificates and Route53 zone IDs.
5. Configure GitHub environments and OIDC role trust.
6. Build and push immutable backend and worker images.
7. Set `TF_VAR_database_url_parameter_value` through an approved secret channel.

Execution after approval:

```bash
infra/scripts/plan.sh staging
ALLOW_TAIGA_TERRAFORM_APPLY=yes infra/scripts/apply.sh staging
```

Production follows the same workflow after staging smoke tests pass.

