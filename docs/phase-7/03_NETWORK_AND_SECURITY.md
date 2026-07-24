# Network And Security

The VPC layout uses public subnets for ALB and private subnets for ECS and RDS.

Security group intent:

- ALB accepts public HTTP/HTTPS.
- Backend accepts only ALB traffic on the application port.
- Worker has no inbound public ingress.
- RDS accepts PostgreSQL only from backend and worker security groups.

Production enables NAT by default for private subnet egress. Staging leaves NAT disabled
by default to reduce accidental cost until deployment planning is complete.

