from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from sqlalchemy import text
from sqlalchemy.orm import Session

from taiga.curriculum_seed import json_text, stable_uuid

SCHEDULE_START = date(2026, 7, 27)
SCHEDULE_END = date(2027, 3, 26)
JST_OFFSET = "+09:00"
OFFICIAL_REQUIREMENTS_URL = "https://42tokyo.jp/requirements/"
APPLY_URL = "https://apply.42tokyo.jp/users/sign_up"


def _fixed_items_path() -> Path:
    return Path(__file__).parent / "seed_data" / "schedule" / "fixed_items.json"


def _due_at(day: date, due_time: str | None = None) -> datetime | None:
    if due_time is None:
        return None
    hour, minute = (int(part) for part in due_time.split(":", maxsplit=1))
    return datetime.fromisoformat(
        f"{day.isoformat()}T{hour:02d}:{minute:02d}:00{JST_OFFSET}"
    ).astimezone(UTC)


def _metadata(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "objective": item.get("objective") or item["description"],
        "deliverables": item.get("deliverables", []),
        "acceptanceCriteria": item.get("acceptanceCriteria", []),
        "allowedEvidenceTypes": item.get("allowedEvidenceTypes", []),
        "nextAction": item.get("nextAction") or "成果物を提出し、Shomaの承認を受ける",
    }


def _upsert_item(
    session: Session,
    *,
    key: str,
    learner_id: uuid.UUID,
    scheduled_date: date,
    title: str,
    description: str,
    item_type: str,
    priority: int,
    assignment_id: uuid.UUID | None = None,
    milestone_key: str | None = None,
    due_at: datetime | None = None,
    source_url: str | None = None,
    is_required: bool = True,
    status_override: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    session.execute(
        text(
            """
            INSERT INTO schedule_items (
                id, schedule_key, learner_id, scheduled_date, title, description,
                item_type, assignment_id, milestone_key, status_override, priority,
                due_at, source_url, is_required, metadata_json
            )
            VALUES (
                :id, :schedule_key, :learner_id, :scheduled_date, :title, :description,
                :item_type, :assignment_id, :milestone_key, :status_override, :priority,
                :due_at, :source_url, :is_required, CAST(:metadata_json AS jsonb)
            )
            ON CONFLICT (schedule_key) DO UPDATE
            SET learner_id = EXCLUDED.learner_id,
                scheduled_date = EXCLUDED.scheduled_date,
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                item_type = EXCLUDED.item_type,
                assignment_id = EXCLUDED.assignment_id,
                milestone_key = EXCLUDED.milestone_key,
                status_override = EXCLUDED.status_override,
                priority = EXCLUDED.priority,
                due_at = EXCLUDED.due_at,
                source_url = EXCLUDED.source_url,
                is_required = EXCLUDED.is_required,
                metadata_json = EXCLUDED.metadata_json,
                updated_at = now()
            """
        ),
        {
            "id": stable_uuid("schedule-item", key),
            "schedule_key": key,
            "learner_id": learner_id,
            "scheduled_date": scheduled_date,
            "title": title,
            "description": description,
            "item_type": item_type,
            "assignment_id": assignment_id,
            "milestone_key": milestone_key,
            "status_override": status_override,
            "priority": priority,
            "due_at": due_at,
            "source_url": source_url,
            "is_required": is_required,
            "metadata_json": json_text(metadata or {}),
        },
    )


def _seed_fixed_items(session: Session, learner_id: uuid.UUID) -> int:
    items = json.loads(_fixed_items_path().read_text(encoding="utf-8"))
    for item in items:
        scheduled_date = date.fromisoformat(item["date"])
        _upsert_item(
            session,
            key=item["key"],
            learner_id=learner_id,
            scheduled_date=scheduled_date,
            title=item["title"],
            description=item["description"],
            item_type=item["itemType"],
            priority=item["priority"],
            milestone_key=item.get("key"),
            due_at=_due_at(scheduled_date, item.get("dueTime")),
            source_url=item.get("sourceUrl"),
            is_required=item.get("isRequired", True),
            metadata=_metadata(item),
        )
    return len(items)


def _seed_curriculum_assignments(session: Session, learner_id: uuid.UUID) -> int:
    rows = (
        session.execute(
            text(
                """
                SELECT a.id AS assignment_id, a.scheduled_date, a.required,
                       t.stable_code, t.title, t.goal, t.instructions_json,
                       t.submission_spec_json
                FROM task_assignments a
                JOIN task_templates t ON t.id = a.task_template_id
                WHERE a.learner_id = :learner_id
                ORDER BY a.scheduled_date, t.stable_code
                """
            ),
            {"learner_id": learner_id},
        )
        .mappings()
        .all()
    )
    for row in rows:
        scheduled_date = row["scheduled_date"]
        instructions = row["instructions_json"]
        submission_spec = row["submission_spec_json"]
        artifacts = cast(
            list[dict[str, Any]],
            submission_spec.get("artifacts", []) if isinstance(submission_spec, dict) else [],
        )
        evidence_types = ["file", "github_url", "screenshot", "text"]
        if scheduled_date < date(2026, 8, 16):
            evidence_types = ["screenshot", "photo", "text", "audio", "video"]
        _upsert_item(
            session,
            key=f"taiga-{scheduled_date.isoformat()}-{row['stable_code'].lower()}",
            learner_id=learner_id,
            scheduled_date=scheduled_date,
            title=row["title"],
            description=row["goal"],
            item_type="assignment",
            assignment_id=row["assignment_id"],
            priority=30 if row["required"] else 70,
            due_at=_due_at(scheduled_date, "23:59"),
            is_required=row["required"],
            metadata={
                "objective": row["goal"],
                "deliverables": [
                    artifact.get("path", "提出物")
                    for artifact in artifacts
                ],
                "acceptanceCriteria": instructions.get("approvalCriteria", []),
                "allowedEvidenceTypes": evidence_types,
                "nextAction": "課題詳細を開いて提出物を作成する",
            },
        )
    return len(rows)


def _fe_pre_pc_item(day: date) -> tuple[str, str]:
    topics = [
        ("基本情報：用語カード作成", "分からない用語を10個選び、自分の言葉で説明する。"),
        ("基本情報：計算問題", "2進数、論理演算、単位変換の問題を解き、計算過程を残す。"),
        ("基本情報：科目A演習", "科目A相当の問題を20問解き、間違い直しを提出する。"),
        ("基本情報：科目B読解", "疑似言語問題を5問読み、処理の流れをノートに書く。"),
        ("復習・再提出回収", "未完了または修正依頼中の成果物を最優先で回収する。"),
        ("週次レビュー準備", "今週の成果物、未完了、質問事項をShomaに見せられる形にする。"),
        ("週次試験", "科目A相当30問と間違い直しを提出する。"),
    ]
    return topics[day.weekday()]


def _seed_pre_pc_days(session: Session, learner_id: uuid.UUID) -> int:
    count = 0
    day = date(2026, 8, 3)
    while day <= date(2026, 8, 15):
        title, description = _fe_pre_pc_item(day)
        _upsert_item(
            session,
            key=f"taiga-{day.isoformat()}-fe-pre-pc",
            learner_id=learner_id,
            scheduled_date=day,
            title=title,
            description=description,
            item_type="assignment" if "週次" not in title and "復習" not in title else "review",
            priority=15,
            due_at=_due_at(day, "23:59"),
            metadata={
                "objective": description,
                "deliverables": ["スクリーンショット", "ノート写真", "回答テキスト"],
                "acceptanceCriteria": [
                    "実施内容が判読できる",
                    "分からない点を隠していない",
                    "Shomaが承認",
                ],
                "allowedEvidenceTypes": ["screenshot", "photo", "text", "audio", "video"],
                "nextAction": "スマホまたはノートで証跡を残して提出する",
            },
        )
        count += 1
        day += timedelta(days=1)
    return count


def _seed_month_end_finance(session: Session, learner_id: uuid.UUID) -> int:
    month_ends = [
        date(2026, 8, 31),
        date(2026, 9, 30),
        date(2026, 10, 31),
        date(2026, 11, 30),
        date(2026, 12, 31),
        date(2027, 1, 31),
        date(2027, 2, 28),
    ]
    for day in month_ends:
        _upsert_item(
            session,
            key=f"taiga-{day.isoformat()}-monthly-savings-check",
            learner_id=learner_id,
            scheduled_date=day,
            title="月末貯金確認",
            description="現在貯金、当月収入、当月支出、目標との差、翌月の必要貯金額を確認する。",
            item_type="finance",
            priority=40,
            due_at=_due_at(day, "23:59"),
            metadata={
                "objective": "上京とPiscine参加に向けた資金状況を隠さず確認する",
                "deliverables": ["現在貯金の証跡", "当月収入", "当月支出", "目標との差"],
                "acceptanceCriteria": ["最低50万円、推奨60万円、安全70万円との差が分かる"],
                "allowedEvidenceTypes": ["screenshot", "photo", "text"],
                "nextAction": "金額を事実として固定せず、確認結果を提出する",
            },
        )
    return len(month_ends)


def _seed_ranges(session: Session, learner_id: uuid.UUID) -> int:
    count = 0
    ranges = [
        (date(2027, 1, 4), date(2027, 1, 10), "上京・入居候補期間", "travel", 10),
        (date(2027, 3, 1), date(2027, 3, 26), "Piscine本番", "piscine", 1),
    ]
    for start, end, title, item_type, priority in ranges:
        day = start
        while day <= end:
            _upsert_item(
                session,
                key=f"taiga-{day.isoformat()}-{item_type}",
                learner_id=learner_id,
                scheduled_date=day,
                title=title,
                description=(
                    "42 Tokyo Piscine本番日。体調、提出、レビュー、翌日の改善を日次で記録する。"
                    if item_type == "piscine"
                    else "上京・入居の候補期間。移動、契約、生活導線確認を進める。"
                ),
                item_type=item_type,
                priority=priority,
                source_url=OFFICIAL_REQUIREMENTS_URL if item_type == "piscine" else None,
                metadata={
                    "objective": title,
                    "deliverables": ["当日の実施記録", "翌日の最優先事項"],
                    "acceptanceCriteria": ["次の行動が明確になっている"],
                    "allowedEvidenceTypes": ["screenshot", "photo", "text"],
                    "nextAction": "当日の結果を記録する",
                },
            )
            count += 1
            day += timedelta(days=1)
    return count


def _seed_empty_day_markers(session: Session, learner_id: uuid.UUID) -> int:
    existing_dates = set(
        session.execute(
            text(
                """
                SELECT DISTINCT scheduled_date
                FROM schedule_items
                WHERE learner_id = :learner_id
                  AND scheduled_date BETWEEN :start_date AND :end_date
                """
            ),
            {"learner_id": learner_id, "start_date": SCHEDULE_START, "end_date": SCHEDULE_END},
        ).scalars()
    )
    count = 0
    day = SCHEDULE_START
    while day <= SCHEDULE_END:
        if day not in existing_dates:
            is_sunday = day.weekday() == 6
            _upsert_item(
                session,
                key=f"taiga-{day.isoformat()}-daily-marker",
                learner_id=learner_id,
                scheduled_date=day,
                title="週次レビュー・未完了回収" if is_sunday else "日次学習・成果物提出",
                description=(
                    "未提出、修正依頼、翌週改善をShomaと確認する。"
                    if is_sunday
                    else "その日の最優先課題に取り組み、成果物または実施証跡を残す。"
                ),
                item_type="review" if is_sunday else "assignment",
                priority=80,
                due_at=_due_at(day, "23:59") if not is_sunday else _due_at(day, "20:00"),
                metadata={
                    "objective": "データなしの日を作らず、未完了を隠さない",
                    "deliverables": ["実施証跡", "未完了理由", "次の行動"],
                    "acceptanceCriteria": ["次にやることが日単位で決まっている"],
                    "allowedEvidenceTypes": ["screenshot", "photo", "text", "file", "github_url"],
                    "nextAction": "未完了があれば今日の最優先として回収する",
                },
            )
            count += 1
        day += timedelta(days=1)
    return count


def seed_schedule_items(
    session: Session,
    *,
    learner_email: str = "taiga@example.local",
) -> int:
    learner_id = session.execute(
        text("SELECT id FROM users WHERE cognito_sub = :learner_email"),
        {"learner_email": learner_email},
    ).scalar_one()
    count = 0
    count += _seed_fixed_items(session, learner_id)
    count += _seed_pre_pc_days(session, learner_id)
    count += _seed_curriculum_assignments(session, learner_id)
    count += _seed_month_end_finance(session, learner_id)
    count += _seed_ranges(session, learner_id)
    count += _seed_empty_day_markers(session, learner_id)
    return count
