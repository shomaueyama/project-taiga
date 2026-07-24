# Rollback Plan

Rollback uses immutable image digests and ECS service updates.

Preferred rollback:

1. Identify the last known good backend and worker image digests.
2. Update Terraform variables or deployment inputs to those digests.
3. Run `terraform plan`.
4. Apply after approval.
5. Run smoke tests.

Database rollback must be migration-specific and must not assume destructive rollback is
safe. Take a snapshot before schema-changing deployments.

