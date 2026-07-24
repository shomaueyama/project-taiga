# Data And Storage

RDS PostgreSQL 17 is modeled with encryption, backups, final snapshots, and production
deletion protection.

S3 buckets are private, encrypted, and public access blocked. The upload bucket enables
versioning. The frontend bucket is intended to be accessed only through CloudFront OAC.

No production data migration was run in this phase.

