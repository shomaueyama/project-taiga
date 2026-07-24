# Security Review

Security posture in this phase:

- Public ingress is limited to CloudFront and ALB.
- Backend ECS accepts traffic only from ALB.
- Worker and RDS have no public ingress.
- S3 buckets block public access.
- Runner is disabled in production.
- LocalAuth is disabled in production runtime variables.

Remaining review items:

- Confirm WAF requirements.
- Confirm VPC endpoint strategy.
- Confirm audit log retention.
- Confirm incident response contacts.

