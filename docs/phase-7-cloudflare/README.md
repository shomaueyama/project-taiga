# Phase 7.1 Cloudflare Assessment

Status: Assessment only - no Cloudflare or AWS resources have been created.

This assessment evaluates whether TAIGA NOVA can move from the Phase 7 AWS foundation to a
Cloudflare-native initial production architecture.

## Documents

- [Repository assessment](00_REPOSITORY_ASSESSMENT.md)
- [Compatibility matrix](01_COMPATIBILITY_MATRIX.md)
- [PostgreSQL to D1 report](02_POSTGRESQL_TO_D1.md)
- [Migration plan](03_MIGRATION_PLAN.md)
- [Cost and limits](04_COST_AND_LIMITS.md)
- [Private repository setup](05_PRIVATE_REPOSITORY_SETUP.md)
- [ADR 0009](../adr/0009-cloudflare-native-initial-production.md)

## Decision

Recommendation: proceed with a hybrid Cloudflare-first assessment path, not an immediate full
Cloudflare-native rewrite.

Effort rating: High.

Critical blocker for immediate full migration: the current backend is Python/FastAPI/SQLAlchemy with
PostgreSQL-specific schema and query behavior. Cloudflare Workers cannot run the current backend
unchanged, and D1 requires a deliberate persistence-layer migration.

