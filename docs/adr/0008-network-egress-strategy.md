# ADR 0008: Network Egress Strategy

Production enables NAT egress for private ECS tasks in the initial Terraform foundation.

Staging disables NAT by default to avoid accidental cost until the account setup is
approved. Phase 8 should evaluate VPC endpoints for S3, ECR, CloudWatch Logs, SSM, and
Secrets Manager to reduce NAT dependency.

