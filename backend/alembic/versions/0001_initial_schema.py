"""Initial Project Taiga schema.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-23
"""

from alembic import op

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE user_role AS ENUM ('learner','reviewer','admin');
CREATE TYPE user_status AS ENUM ('invited','active','suspended','disabled','deleted');
CREATE TYPE curriculum_status AS ENUM ('draft','published','retired');
CREATE TYPE assignment_status AS ENUM ('not_started','available','in_progress','awaiting_submission','completed','missed','cancelled');
CREATE TYPE submission_status AS ENUM ('draft','submitted','queued','running','automated_passed','automated_failed','manual_review_pending','needs_revision','approved','cancelled');
CREATE TYPE runner_status AS ENUM ('queued','claimed','preflight','building','public_testing','hidden_testing','sanitizing','succeeded','failed','timed_out','cancelled','security_rejected');
CREATE TYPE exam_attempt_status AS ENUM ('scheduled','ready','in_progress','submitted','evaluating','oral_pending','passed','failed','expired','cancelled');
CREATE TYPE review_result AS ENUM ('approved','needs_revision');
CREATE TYPE upload_scan_status AS ENUM ('created','uploaded','scanning','accepted','rejected','expired');

CREATE TABLE users (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), cognito_sub text NOT NULL UNIQUE,
 display_name varchar(120) NOT NULL, role user_role NOT NULL,
 status user_status NOT NULL DEFAULT 'invited', timezone varchar(64) NOT NULL DEFAULT 'Asia/Tokyo',
 version integer NOT NULL DEFAULT 1 CHECK(version>0), created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(), deleted_at timestamptz);
CREATE INDEX users_role_status_idx ON users(role,status);

CREATE TABLE curriculum_versions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), version varchar(40) NOT NULL UNIQUE,
 status curriculum_status NOT NULL DEFAULT 'draft', content_hash char(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
 published_at timestamptz, locked_at timestamptz, created_at timestamptz NOT NULL DEFAULT now(),
 CHECK((status='published')=(published_at IS NOT NULL)));

CREATE TABLE weeks (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), curriculum_version_id uuid NOT NULL REFERENCES curriculum_versions(id) ON DELETE RESTRICT,
 stable_code varchar(32) NOT NULL, number smallint NOT NULL CHECK(number BETWEEN 1 AND 52),
 title varchar(200) NOT NULL, goal text NOT NULL, start_date date NOT NULL, end_date date NOT NULL,
 UNIQUE(curriculum_version_id,stable_code), UNIQUE(curriculum_version_id,number), CHECK(start_date<=end_date));

CREATE TABLE task_templates (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), curriculum_version_id uuid NOT NULL REFERENCES curriculum_versions(id) ON DELETE RESTRICT,
 week_id uuid NOT NULL REFERENCES weeks(id) ON DELETE RESTRICT, stable_code varchar(40) NOT NULL,
 title varchar(200) NOT NULL, goal text NOT NULL, instructions_json jsonb NOT NULL,
 submission_spec_json jsonb NOT NULL CHECK(jsonb_typeof(submission_spec_json)='object'),
 oral_check_required boolean NOT NULL DEFAULT false, UNIQUE(curriculum_version_id,stable_code));

CREATE TABLE task_assignments (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), task_template_id uuid NOT NULL REFERENCES task_templates(id) ON DELETE RESTRICT,
 learner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT, scheduled_date date NOT NULL,
 required boolean NOT NULL DEFAULT true, activation_json jsonb NOT NULL DEFAULT '{}'::jsonb,
 status assignment_status NOT NULL DEFAULT 'not_started', version integer NOT NULL DEFAULT 1 CHECK(version>0),
 created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(task_template_id,learner_id));
CREATE INDEX task_assignments_learner_status_date_idx ON task_assignments(learner_id,status,scheduled_date);

CREATE TABLE upload_sessions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), owner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 object_key text NOT NULL UNIQUE, original_name varchar(120) NOT NULL, declared_media_type varchar(120) NOT NULL,
 detected_media_type varchar(120), declared_size_bytes bigint NOT NULL CHECK(declared_size_bytes BETWEEN 0 AND 52428800),
 actual_size_bytes bigint CHECK(actual_size_bytes BETWEEN 0 AND 52428800),
 declared_sha256 char(64) NOT NULL CHECK(declared_sha256~'^[0-9a-f]{64}$'),
 actual_sha256 char(64) CHECK(actual_sha256~'^[0-9a-f]{64}$'),
 scan_status upload_scan_status NOT NULL DEFAULT 'created', rejection_code varchar(80),
 expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), completed_at timestamptz);
CREATE INDEX upload_sessions_owner_status_idx ON upload_sessions(owner_id,scan_status,created_at);

CREATE TABLE submissions (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), assignment_id uuid NOT NULL REFERENCES task_assignments(id) ON DELETE RESTRICT,
 learner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT, submission_version integer NOT NULL CHECK(submission_version>0),
 source_type varchar(30) NOT NULL CHECK(source_type IN ('public_git','zip_upload','file_upload')),
 repository_url text, commit_hash char(40) CHECK(commit_hash~'^[0-9a-f]{40}$'),
 artifact_manifest_json jsonb NOT NULL CHECK(jsonb_typeof(artifact_manifest_json)='object'),
 status submission_status NOT NULL DEFAULT 'submitted', created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(assignment_id,submission_version),
 CHECK((source_type='public_git' AND repository_url IS NOT NULL AND commit_hash IS NOT NULL) OR source_type IN ('zip_upload','file_upload')));
CREATE INDEX submissions_learner_created_idx ON submissions(learner_id,created_at DESC);

CREATE TABLE submission_artifacts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), submission_id uuid NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
 upload_session_id uuid REFERENCES upload_sessions(id) ON DELETE RESTRICT, s3_key text NOT NULL UNIQUE,
 sha256 char(64) NOT NULL CHECK(sha256~'^[0-9a-f]{64}$'), media_type varchar(120) NOT NULL,
 size_bytes bigint NOT NULL CHECK(size_bytes BETWEEN 0 AND 52428800), original_name varchar(120) NOT NULL);
CREATE INDEX submission_artifacts_submission_idx ON submission_artifacts(submission_id);

CREATE TABLE runner_jobs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), submission_id uuid NOT NULL REFERENCES submissions(id) ON DELETE RESTRICT,
 status runner_status NOT NULL DEFAULT 'queued', attempt smallint NOT NULL CHECK(attempt BETWEEN 1 AND 5),
 image_digest varchar(100) NOT NULL, security_profile_version varchar(40) NOT NULL,
 queued_at timestamptz NOT NULL DEFAULT now(), started_at timestamptz, finished_at timestamptz,
 resource_usage_json jsonb NOT NULL DEFAULT '{}'::jsonb, sanitized_result_json jsonb,
 internal_result_s3_key text, failure_code varchar(80), version integer NOT NULL DEFAULT 1 CHECK(version>0),
 UNIQUE(submission_id,attempt), CHECK(finished_at IS NULL OR started_at IS NOT NULL),
 CHECK(finished_at IS NULL OR finished_at>=started_at));
CREATE INDEX runner_jobs_status_queued_idx ON runner_jobs(status,queued_at);

CREATE TABLE reviews (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), submission_id uuid NOT NULL REFERENCES submissions(id) ON DELETE RESTRICT,
 reviewer_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT, result review_result NOT NULL,
 rubric_json jsonb NOT NULL CHECK(jsonb_typeof(rubric_json)='object'), comment text NOT NULL,
 oral_result_json jsonb, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX reviews_submission_created_idx ON reviews(submission_id,created_at DESC);

CREATE TABLE exams (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), curriculum_version_id uuid NOT NULL REFERENCES curriculum_versions(id) ON DELETE RESTRICT,
 week_id uuid NOT NULL REFERENCES weeks(id) ON DELETE RESTRICT, stable_code varchar(40) NOT NULL,
 blueprint_json jsonb NOT NULL CHECK(jsonb_typeof(blueprint_json)='object'), scheduled_at timestamptz NOT NULL,
 UNIQUE(curriculum_version_id,stable_code));

CREATE TABLE exam_variants (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), exam_id uuid NOT NULL REFERENCES exams(id) ON DELETE RESTRICT,
 stable_code varchar(60) NOT NULL, version integer NOT NULL CHECK(version>0),
 problem_snapshot_json jsonb NOT NULL CHECK(jsonb_typeof(problem_snapshot_json)='object'),
 hidden_test_s3_key text NOT NULL, content_hash char(64) NOT NULL CHECK(content_hash~'^[0-9a-f]{64}$'),
 active boolean NOT NULL DEFAULT true, UNIQUE(exam_id,stable_code,version));

CREATE TABLE exam_attempts (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), exam_id uuid NOT NULL REFERENCES exams(id) ON DELETE RESTRICT,
 exam_variant_id uuid NOT NULL REFERENCES exam_variants(id) ON DELETE RESTRICT,
 learner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT, attempt_number smallint NOT NULL CHECK(attempt_number BETWEEN 1 AND 10),
 status exam_attempt_status NOT NULL DEFAULT 'scheduled', variant_snapshot_json jsonb NOT NULL,
 starts_at timestamptz, deadline_at timestamptz, submitted_at timestamptz,
 final_submission_id uuid REFERENCES submissions(id) ON DELETE RESTRICT,
 oral_result_json jsonb, result_json jsonb, version integer NOT NULL DEFAULT 1 CHECK(version>0),
 created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(exam_id,learner_id,attempt_number),
 CHECK(deadline_at IS NULL OR starts_at IS NOT NULL), CHECK(deadline_at IS NULL OR deadline_at>starts_at),
 CHECK(submitted_at IS NULL OR starts_at IS NOT NULL));
CREATE INDEX exam_attempts_learner_status_idx ON exam_attempts(learner_id,status,created_at DESC);

CREATE TABLE capability_achievements (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), learner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 capability_code varchar(60) NOT NULL, level smallint NOT NULL CHECK(level BETWEEN 0 AND 10),
 evidence_json jsonb NOT NULL CHECK(jsonb_typeof(evidence_json)='array'), achieved_at timestamptz NOT NULL,
 UNIQUE(learner_id,capability_code,level));

CREATE TABLE rank_history (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), learner_id uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 rank_code varchar(40) NOT NULL, evidence_snapshot_json jsonb NOT NULL CHECK(jsonb_typeof(evidence_snapshot_json)='object'),
 achieved_at timestamptz NOT NULL);
CREATE INDEX rank_history_learner_idx ON rank_history(learner_id,achieved_at DESC);

CREATE TABLE idempotency_keys (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), actor_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 route varchar(200) NOT NULL, key varchar(128) NOT NULL, request_hash char(64) NOT NULL CHECK(request_hash~'^[0-9a-f]{64}$'),
 response_status integer, response_body jsonb, expires_at timestamptz NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(actor_id,route,key));

CREATE TABLE audit_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), occurred_at timestamptz NOT NULL DEFAULT now(),
 actor_id uuid REFERENCES users(id) ON DELETE SET NULL, actor_role user_role, action varchar(120) NOT NULL,
 entity_type varchar(80) NOT NULL, entity_id uuid, request_id varchar(100), source_ip inet,
 before_json jsonb, after_json jsonb, outcome varchar(20) NOT NULL CHECK(outcome IN ('success','denied','failed')));
CREATE INDEX audit_events_entity_idx ON audit_events(entity_type,entity_id,occurred_at DESC);
CREATE INDEX audit_events_actor_idx ON audit_events(actor_id,occurred_at DESC);

CREATE TABLE outbox_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), aggregate_type varchar(80) NOT NULL, aggregate_id uuid NOT NULL,
 event_type varchar(120) NOT NULL, payload_json jsonb NOT NULL CHECK(jsonb_typeof(payload_json)='object'),
 created_at timestamptz NOT NULL DEFAULT now(), published_at timestamptz,
 attempt_count integer NOT NULL DEFAULT 0 CHECK(attempt_count>=0), next_attempt_at timestamptz NOT NULL DEFAULT now(),
 last_error text);
CREATE INDEX outbox_unpublished_idx ON outbox_events(next_attempt_at,created_at) WHERE published_at IS NULL;

CREATE TABLE ai_usage_reports (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), submission_id uuid NOT NULL UNIQUE REFERENCES submissions(id) ON DELETE CASCADE,
 provider varchar(80) NOT NULL, model varchar(120) NOT NULL, purpose text NOT NULL,
 prompt_summary text NOT NULL, output_usage_summary text NOT NULL, learner_explanation text NOT NULL,
 declared_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE notifications (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 type varchar(80) NOT NULL, title varchar(200) NOT NULL, body text NOT NULL, entity_type varchar(80), entity_id uuid,
 deduplication_key varchar(240) NOT NULL UNIQUE, read_at timestamptz, created_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX notifications_user_unread_idx ON notifications(user_id,created_at DESC) WHERE read_at IS NULL;

CREATE TABLE notification_preferences (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 channel varchar(30) NOT NULL CHECK(channel IN ('in_app','email')), event_type varchar(80) NOT NULL,
 enabled boolean NOT NULL DEFAULT true, UNIQUE(user_id,channel,event_type));

CREATE TABLE feature_flags (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), key varchar(100) NOT NULL UNIQUE,
 enabled boolean NOT NULL DEFAULT false, rules_json jsonb NOT NULL DEFAULT '{}'::jsonb,
 version integer NOT NULL DEFAULT 1 CHECK(version>0), updated_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 updated_at timestamptz NOT NULL DEFAULT now());

CREATE TABLE analytics_events (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), event_name varchar(120) NOT NULL,
 occurred_at timestamptz NOT NULL, pseudonymous_user_id char(64), session_id uuid,
 properties_json jsonb NOT NULL DEFAULT '{}'::jsonb);
CREATE INDEX analytics_events_name_time_idx ON analytics_events(event_name,occurred_at);

CREATE TABLE curriculum_import_jobs (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), curriculum_version varchar(40) NOT NULL,
 status varchar(40) NOT NULL CHECK(status IN ('uploaded','validating','invalid','ready','publishing','published','failed')),
 dry_run boolean NOT NULL, source_sha256 char(64) NOT NULL CHECK(source_sha256~'^[0-9a-f]{64}$'),
 diff_summary_json jsonb, validation_result_json jsonb NOT NULL,
 created_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
 created_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz);
CREATE INDEX curriculum_import_jobs_status_created_idx ON curriculum_import_jobs(status,created_at DESC);
        """
    )


def downgrade() -> None:
    raise RuntimeError(
        "Destructive rollback is prohibited after learner data exists. "
        "Restore a backup or issue a corrective migration."
    )
