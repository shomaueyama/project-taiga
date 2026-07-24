# ADR 0007: Use Immutable Image Digests

Production deployments should reference ECR images by digest.

Mutable tags are acceptable for local development but are not precise enough for rollback
or audit in production.

