from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text

from alembic import command
from taiga.curriculum_seed import seed
from taiga.infrastructure.database import SessionLocal
from taiga.main import app
from taiga.schedule_domain import (
    ScheduleStateInput,
    calculate_schedule_state,
    representative_status,
)


def migrate() -> None:
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[1] / "alembic"))
    command.upgrade(config, "head")


def headers(email: str = "taiga@example.local") -> dict[str, str]:
    return {"Authorization": f"Bearer local:{email}", "Idempotency-Key": f"schedule-{email}"}


@pytest.fixture(scope="module")
def seeded_schedule() -> None:
    migrate()
    curriculum_file = (
        Path(__file__).parents[3]
        / "design/taiga-42-v4.0-implementation-pack/curriculum/weeks.json"
    )
    if not curriculum_file.exists():
        pytest.skip("Design curriculum is not present in this checkout")
    seed()
    seed()


def test_schedule_seed_has_daily_records_and_required_milestones(seeded_schedule: None) -> None:
    with SessionLocal() as session:
        distinct_days = int(
            session.execute(
                text(
                    """
                    SELECT count(DISTINCT scheduled_date)
                    FROM schedule_items s
                    JOIN users u ON u.id = s.learner_id
                    WHERE u.cognito_sub = 'taiga@example.local'
                      AND scheduled_date BETWEEN '2026-07-27' AND '2027-03-26'
                    """
                )
            ).scalar_one()
        )
        assert distinct_days == (date(2027, 3, 26) - date(2026, 7, 27)).days + 1
        keys = set(
            session.execute(
                text(
                    """
                    SELECT schedule_key
                    FROM schedule_items
                    WHERE schedule_key IN (
                      'taiga-2026-09-05-open-school',
                      'taiga-2026-08-24-42-web-test',
                      'taiga-2026-10-03-fe-exam',
                      'taiga-2027-01-11-tokyo-commute-check',
                      'taiga-2027-03-01-piscine'
                    )
                    """
                )
            ).scalars()
        )
        assert keys == {
            "taiga-2026-09-05-open-school",
            "taiga-2026-08-24-42-web-test",
            "taiga-2026-10-03-fe-exam",
            "taiga-2027-01-11-tokyo-commute-check",
            "taiga-2027-03-01-piscine",
        }


def test_schedule_api_returns_month_days_and_assignment_links(seeded_schedule: None) -> None:
    response = TestClient(app).get(
        "/api/v1/schedule?from=2026-07-27&to=2026-08-02",
        headers=headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["days"]) == 7
    first_day = body["days"][0]
    assert first_day["date"] == "2026-07-27"
    assert first_day["items"][0]["title"] == "基本情報：ハードウェア現在地確認"
    assert first_day["items"][0]["metadata"]["allowedEvidenceTypes"] == [
        "screenshot",
        "photo",
        "text",
    ]
    second_day = body["days"][1]
    assert second_day["date"] == "2026-07-28"
    assert second_day["items"][0]["title"] == "基本情報：ハードウェア範囲完了判定"


def test_schedule_day_and_summary_are_available_to_admin(seeded_schedule: None) -> None:
    client = TestClient(app)
    day = client.get("/api/v1/schedule/2026-09-05", headers=headers("admin@example.local"))
    assert day.status_code == 200
    titles = {item["title"] for item in day.json()["items"]}
    assert "42 Tokyo現地見学・学校説明会" in titles
    assert "Introduction Meeting参加要否確認" in titles

    summary = client.get("/api/v1/schedule/summary", headers=headers("admin@example.local"))
    assert summary.status_code == 200
    assert summary.json()["nextImportantDate"] == "2026-08-24"
    assert summary.json()["nextImportantTitle"] == "42 Tokyo Webテスト本番"
    assert summary.json()["daysUntilPiscine"] > 0


def test_admin_can_create_update_cancel_and_delete_schedule_items(seeded_schedule: None) -> None:
    client = TestClient(app)
    create = client.post(
        "/api/v1/admin/schedule-items",
        headers=headers("admin@example.local"),
        json={
            "date": "2026-09-07",
            "title": "追加確認",
            "description": "Shomaが追加した確認予定。",
            "itemType": "application",
            "priority": 7,
            "dueAt": "2026-09-07T23:59:00+09:00",
            "isRequired": True,
            "metadata": {
                "deliverables": ["確認結果"],
                "acceptanceCriteria": ["次の行動が決まる"],
                "allowedEvidenceTypes": ["text"],
            },
        },
    )
    assert create.status_code == 201
    item_id = create.json()["id"]
    assert create.json()["title"] == "追加確認"

    update = client.patch(
        f"/api/v1/admin/schedule-items/{item_id}",
        headers=headers("admin@example.local"),
        json={"title": "追加確認・更新済み", "priority": 5},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "追加確認・更新済み"
    assert update.json()["priority"] == 5

    cancel_target = client.get(
        "/api/v1/schedule/2026-09-30",
        headers=headers("admin@example.local"),
    )
    assert cancel_target.status_code == 200
    target_id = next(
        item["id"]
        for item in cancel_target.json()["items"]
        if item["scheduleKey"] == "taiga-2026-09-30-introduction-meeting-candidate"
    )
    cancel = client.patch(
        f"/api/v1/admin/schedule-items/{target_id}",
        headers=headers("admin@example.local"),
        json={"statusOverride": "cancelled", "isRequired": False},
    )
    assert cancel.status_code == 200
    assert cancel.json()["displayStatus"] == "cancelled"

    restore = client.patch(
        f"/api/v1/admin/schedule-items/{target_id}",
        headers=headers("admin@example.local"),
        json={"statusOverride": None, "isRequired": True},
    )
    assert restore.status_code == 200
    assert restore.json()["displayStatus"] != "cancelled"

    delete = client.delete(
        f"/api/v1/admin/schedule-items/{item_id}",
        headers=headers("admin@example.local"),
    )
    assert delete.status_code == 204

    forbidden = client.post(
        "/api/v1/admin/schedule-items",
        headers=headers(),
        json={
            "date": "2026-09-08",
            "title": "learner write",
            "itemType": "milestone",
        },
    )
    assert forbidden.status_code == 403


def test_schedule_state_distinguishes_learner_and_review_overdue() -> None:
    now = datetime(2026, 7, 29, 12, 0, tzinfo=UTC)
    due_at = now - timedelta(days=2)
    learner = calculate_schedule_state(
        ScheduleStateInput(
            scheduled_date=date(2026, 7, 27),
            item_type="assignment",
            due_at=due_at,
            status_override=None,
            assignment_status="in_progress",
            latest_submission_status=None,
        ),
        now=now,
    )
    review = calculate_schedule_state(
        ScheduleStateInput(
            scheduled_date=date(2026, 7, 27),
            item_type="assignment",
            due_at=due_at,
            status_override=None,
            assignment_status="in_progress",
            latest_submission_status="manual_review_pending",
        ),
        now=now,
    )
    approved = calculate_schedule_state(
        ScheduleStateInput(
            scheduled_date=date(2026, 7, 27),
            item_type="assignment",
            due_at=due_at,
            status_override=None,
            assignment_status="completed",
            latest_submission_status="approved",
        ),
        now=now,
    )
    assert learner.display_status == "learner_overdue"
    assert review.display_status == "review_overdue"
    assert approved.display_status == "approved"
    assert approved.is_overdue is False
    assert (
        representative_status(["approved", "revision_requested", "review_waiting"])
        == "revision_requested"
    )
