"""Add Phase 5 performance indexes.

Revision ID: 0002_phase5_performance_indexes
Revises: 0001_initial_schema
Create Date: 2026-07-23
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_phase5_performance_indexes"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "outbox_unpublished_type_due_idx",
        "outbox_events",
        ["event_type", "next_attempt_at", "created_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("outbox_unpublished_type_due_idx", table_name="outbox_events")
