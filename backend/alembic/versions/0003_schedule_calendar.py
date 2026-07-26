"""Add local schedule calendar.

Revision ID: 0003_schedule_calendar
Revises: 0002_phase5_performance_indexes
Create Date: 2026-07-26
"""

from alembic import op

revision = "0003_schedule_calendar"
down_revision = "0002_phase5_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
CREATE TABLE schedule_items (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 schedule_key varchar(120) NOT NULL UNIQUE,
 learner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 scheduled_date date NOT NULL,
 start_at timestamptz,
 end_at timestamptz,
 title varchar(240) NOT NULL,
 description text NOT NULL DEFAULT '',
 item_type varchar(40) NOT NULL CHECK(item_type IN (
   'assignment','exam','application','orientation','housing','finance','travel',
   'piscine','milestone','rest','review'
 )),
 assignment_id uuid REFERENCES task_assignments(id) ON DELETE SET NULL,
 milestone_key varchar(120),
 status_override varchar(40) CHECK(status_override IN (
   'not_started','in_progress','submitted','revision_requested','approved','cancelled'
 )),
 priority smallint NOT NULL DEFAULT 50 CHECK(priority BETWEEN 1 AND 100),
 due_at timestamptz,
 source_url text,
 is_required boolean NOT NULL DEFAULT true,
 metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb CHECK(jsonb_typeof(metadata_json)='object'),
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(end_at IS NULL OR start_at IS NULL OR end_at >= start_at)
);
CREATE INDEX schedule_items_learner_date_idx ON schedule_items(learner_id, scheduled_date, priority);
CREATE INDEX schedule_items_assignment_idx ON schedule_items(assignment_id) WHERE assignment_id IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.drop_index("schedule_items_assignment_idx", table_name="schedule_items")
    op.drop_index("schedule_items_learner_date_idx", table_name="schedule_items")
    op.drop_table("schedule_items")
