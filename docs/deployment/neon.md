# Neon PostgreSQL Deployment

Status: plan only. No Neon project or database was created.

## Setup

After Gate B approval:

1. Create a Neon project and production database.
2. Copy the pooled or direct PostgreSQL connection string from Neon.
3. Configure Render `DATABASE_URL` and `MIGRATION_DATABASE_URL` without committing either value.
4. Ensure SSL is required.
5. Confirm `alembic heads` before Gate C.
6. Apply migrations only after Gate C approval.

The backend normalizes `postgres://` and `postgresql://` to `postgresql+psycopg://` for SQLAlchemy.

## Free-Tier Notes

The owner must verify the dashboard before launch because provider limits and pricing can change.
Neon Free currently has constrained storage/compute behavior, including scale-to-zero behavior and
limited backup/snapshot capabilities.

Official references:

- https://neon.com/docs/introduction/plans
- https://neon.com/docs/introduction/usage-calculations
- https://neon.com/docs/guides/scale-to-zero-guide
- https://neon.com/docs/guides/backup-restore
