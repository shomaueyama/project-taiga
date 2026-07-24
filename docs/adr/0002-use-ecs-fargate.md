# ADR 0002: Use ECS Fargate

Backend and worker production runtimes use ECS Fargate.

This avoids host management while keeping deployment close to Docker Compose service
boundaries from the local MVP.

