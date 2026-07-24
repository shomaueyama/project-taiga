# Target Architecture

The target production architecture is:

- Route53 for DNS.
- ACM certificates for HTTPS.
- CloudFront and private S3 bucket for frontend hosting.
- ALB for backend HTTPS ingress.
- ECS Fargate services for backend and worker.
- RDS PostgreSQL 17 for relational state.
- S3 bucket for uploads and artifacts.
- ECR repositories for immutable images.
- SSM Parameter Store or Secrets Manager for secrets.
- CloudWatch logs, alarms, and dashboard.
- GitHub Actions OIDC for deployment identity.

Runner execution remains disabled in production until hostile runner tests and an isolated
AWS runner architecture are approved.

