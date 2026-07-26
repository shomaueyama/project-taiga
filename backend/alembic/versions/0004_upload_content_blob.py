"""Store uploaded file content for assignment evidence.

Revision ID: 0004_upload_content_blob
Revises: 0003_schedule_calendar
Create Date: 2026-07-26
"""

from alembic import op

revision = "0004_upload_content_blob"
down_revision = "0003_schedule_calendar"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE upload_sessions ADD COLUMN IF NOT EXISTS uploaded_blob bytea")


def downgrade() -> None:
    op.execute("ALTER TABLE upload_sessions DROP COLUMN IF EXISTS uploaded_blob")
