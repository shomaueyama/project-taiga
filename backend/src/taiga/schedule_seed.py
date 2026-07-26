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
        artifact_paths = [artifact.get("path", "提出物") for artifact in artifacts]
        evidence_types = ["file", "github_url", "screenshot", "text"]
        if scheduled_date < date(2026, 8, 16):
            evidence_types = ["screenshot", "photo", "text", "audio", "video"]
        generated_deliverables = [
            *(artifact_paths or ["回答またはコード"]),
            "実行結果または採点結果のスクリーンショット",
            "自分で確認したテストケース3件",
            "詰まった点と調べたこと",
            "次に直す点または次に進む範囲",
        ]
        generated_criteria = [
            *instructions.get("approvalCriteria", []),
            "提出物を第三者が開いて確認できる",
            "実行結果または採点結果の証跡がある",
            "テストケース3件で確認している",
            "詰まった点を隠さず書いている",
        ]
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
                "deliverables": generated_deliverables,
                "acceptanceCriteria": generated_criteria,
                "allowedEvidenceTypes": evidence_types,
                "nextAction": "学習記録に成果物、実行証跡、詰まった点を提出する",
            },
        )
    return len(rows)


def _fe_pre_pc_item(day: date) -> tuple[str, str, list[str], list[str]]:
    topics = [
        (
            "基本情報：用語カード作成",
            "分からない用語を10個選び、自分の言葉で説明する。",
            ["用語10個", "各用語の自分の説明", "理解できた/未理解の区分"],
            ["10語すべてに説明がある", "未理解語に翌日の確認方法がある"],
        ),
        (
            "基本情報：計算問題",
            "2進数、論理演算、単位変換の問題を合計20問解き、計算過程を残す。",
            ["計算問題20問の正答数", "途中式の写真またはテキスト", "間違い直し全問"],
            ["20問解いた証跡がある", "途中式で解法を追える", "間違い直しが全問ある"],
        ),
        (
            "基本情報：科目A演習",
            "科目A相当の問題を25問解き、正答数、正答率、間違い直しを提出する。",
            ["科目A25問の正答数と正答率", "採点結果スクリーンショット", "間違い直し全問"],
            ["25問解いた証跡がある", "正答率が数字で分かる", "間違い直しが全問ある"],
        ),
        (
            "基本情報：科目B読解",
            "擬似言語問題を5問読み、処理の流れと変数の変化をノートに書く。",
            ["科目B相当5問の正答数", "変数追跡メモ2問分", "間違い直し全問"],
            ["5問解いた証跡がある", "変数の変化を追っている", "間違い直しが全問ある"],
        ),
        (
            "復習・再提出回収",
            "未完了または修正依頼中の成果物を最優先で回収し、残件を0に近づける。",
            ["未完了一覧", "回収した提出物", "残件と再提出日"],
            ["未完了を隠していない", "回収結果が確認できる", "残件に日付がある"],
        ),
        (
            "週次レビュー準備",
            "今週の成果物、未完了、質問事項をShomaに見せられる形に整理する。",
            ["今週の提出一覧", "未完了一覧", "質問3つ", "翌週の重点3つ"],
            ["提出状況を一覧で確認できる", "質問と翌週重点が具体的である"],
        ),
        (
            "週次試験",
            "科目A相当30問と科目B相当5問を解き、間違い直しを提出する。",
            ["科目A30問の正答数", "科目B5問の正答数", "採点証跡", "間違い直し全問"],
            ["科目A/Bの両方を解いている", "正答数が数字で分かる", "間違い直しが全問ある"],
        ),
    ]
    return topics[day.weekday()]


def _seed_pre_pc_days(session: Session, learner_id: uuid.UUID) -> int:
    count = 0
    day = date(2026, 8, 3)
    while day <= date(2026, 8, 15):
        title, description, deliverables, criteria = _fe_pre_pc_item(day)
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
                "deliverables": deliverables,
                "acceptanceCriteria": criteria,
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
                "deliverables": [
                    "現在貯金額の証跡",
                    "当月収入と当月支出",
                    "50万円・60万円・70万円との差額",
                    "翌月に増やす貯金額",
                ],
                "acceptanceCriteria": [
                    "金額が数字で書かれている",
                    "証跡で確認できる",
                    "翌月の改善アクションが金額つきである",
                ],
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
                    "deliverables": (
                        [
                            "当日の課題提出または演習ログ",
                            "レビューを受けた件数",
                            "詰まった点と調べたこと",
                            "翌日の最優先事項",
                        ]
                        if item_type == "piscine"
                        else [
                            "移動または生活導線の確認結果",
                            "写真またはスクリーンショット",
                            "未解決事項と次の行動",
                            "翌日に確認する場所または手続き",
                        ]
                    ),
                    "acceptanceCriteria": (
                        [
                            "当日取り組んだ内容が証跡で分かる",
                            "レビュー/詰まり/翌日タスクが書かれている",
                            "翌日すぐ動ける状態になっている",
                        ]
                        if item_type == "piscine"
                        else [
                            "移動・生活上の確認結果が具体的である",
                            "未解決事項に期限がある",
                            "翌日の確認対象が決まっている",
                        ]
                    ),
                    "allowedEvidenceTypes": ["screenshot", "photo", "text"],
                    "nextAction": "当日の結果を記録する",
                },
            )
            count += 1
            day += timedelta(days=1)
    return count


def _daily_marker_plan(day: date) -> tuple[str, str, str, list[str], list[str], list[str]]:
    weekday = day.weekday()
    if day < date(2026, 8, 16):
        title, description, deliverables, criteria = _fe_pre_pc_item(day)
        return title, description, "assignment" if weekday < 5 else "review", deliverables, criteria, [
            "screenshot",
            "photo",
            "text",
        ]
    if day < date(2026, 8, 24):
        plans = [
            (
                "Piscine準備：ターミナル反復",
                "pwd/ls/cd/mkdir/touch/cat/rm/grep相当を手で打ち、用途を説明する。",
                ["コマンド8個の実行ログ", "各コマンドの用途", "失敗した操作と修正"],
                ["8個以上を実行している", "用途を自分の言葉で説明している"],
            ),
            (
                "Piscine準備：Git反復",
                "clone/add/commit/status/log/diff/pushを1周し、履歴を確認する。",
                ["Git操作1周のログ", "commit hash", "GitHub画面スクリーンショット"],
                ["push結果が確認できる", "status/log/diffの意味を書いている"],
            ),
            (
                "Piscine準備：C基礎演習",
                "Cの小問10問を解き、コンパイルと実行を繰り返す。",
                ["C小問10問の成功数", "コンパイルログ", "失敗した問題の原因"],
                ["10問取り組んでいる", "7問以上コンパイル成功、または失敗原因が全問ある"],
            ),
            (
                "Piscine準備：エラー修正",
                "Cのコンパイルエラーと実行時の想定違いを3件作り、直し方を記録する。",
                ["エラー3件", "修正前後のコード", "修正理由", "再発防止メモ"],
                ["3件とも修正理由がある", "同じミスを防ぐメモがある", "修正後に実行確認している"],
            ),
            (
                "Piscine準備：説明練習",
                "今日書いたコードまたはコマンドを、Shomaに説明できる形にまとめる。",
                ["説明メモ3点", "コードまたはログ", "処理の流れ", "質問したい点"],
                ["第三者が内容を追える", "質問が具体的である", "処理の入口と出口を説明している"],
            ),
            (
                "Piscine準備：制限時間演習",
                "45分でターミナル/Git/Cの小課題を1題解き、時間内に提出する。",
                ["開始時刻と終了時刻", "提出物", "実行結果", "時間切れの場合の原因"],
                ["45分以内の取り組みが分かる", "実行結果を確認できる", "時間切れ時の改善がある"],
            ),
            (
                "週次確認：実操作レビュー",
                "ターミナル、Git、Cの実操作を週次で確認し、翌週の弱点を決める。",
                ["Git操作1周", "C小問15問の結果", "弱点3つ"],
                ["Git操作が通っている", "C小問の成功数が分かる", "弱点が具体的である"],
            ),
        ]
        title, description, deliverables, criteria = plans[weekday]
        return title, description, "assignment" if weekday < 6 else "review", deliverables, criteria, [
            "screenshot",
            "text",
            "github_url",
        ]
    if day < date(2026, 10, 4):
        plans = [
            (
                "基本情報：科目A演習40問",
                "科目A相当40問を解き、弱点分野と間違い直しを残す。",
                ["科目A40問の正答数", "採点スクリーンショット", "間違い直し全問"],
                ["40問解いた証跡がある", "正答率と弱点分野が書かれている"],
            ),
            (
                "基本情報：科目Bアルゴリズム10問",
                "科目B相当の擬似言語・変数追跡を10問解く。",
                ["科目B10問の正答数", "変数追跡メモ3問分", "間違い直し全問"],
                ["10問解いた証跡がある", "変数追跡を説明できる"],
            ),
            (
                "Piscine準備：C演習15問",
                "FE学習と並行してC小問15問をコンパイルまで行う。",
                ["C小問15問の成功数", "コンパイルログ", "失敗原因"],
                ["15問取り組んでいる", "10問以上成功または原因整理がある"],
            ),
            (
                "基本情報：弱点分野回収",
                "直近の誤答から弱点2分野を選び、各15問ずつ解く。",
                ["弱点2分野", "各15問の正答数", "間違い直し"],
                ["合計30問解いている", "弱点の理由が書かれている"],
            ),
            (
                "科目B：情報セキュリティ演習",
                "科目Bの情報セキュリティ相当問題を5問、関連する科目Aを15問解く。",
                ["科目Bセキュリティ5問", "科目A関連15問", "誤答メモ"],
                ["合計20問の結果がある", "セキュリティ用語を説明できる"],
            ),
            (
                "模試：FE短縮セット",
                "科目A30問・科目B10問を時間を測って解く。",
                ["開始/終了時刻", "科目A30問の正答数", "科目B10問の正答数", "誤答全問直し"],
                ["時間を測っている", "両科目の正答数が分かる", "誤答直しがある"],
            ),
            (
                "週次確認：FE/Piscine両立レビュー",
                "FEの点数推移とC/Git実操作の継続状況を確認する。",
                ["今週の問題数合計", "科目A/Bの正答率推移", "C/Git実操作日数", "翌週重点3つ"],
                ["数値で推移を確認できる", "翌週重点が具体的である"],
            ),
        ]
        title, description, deliverables, criteria = plans[weekday]
        return title, description, "assignment" if weekday < 6 else "review", deliverables, criteria, [
            "screenshot",
            "photo",
            "text",
            "github_url",
        ]
    if day < date(2027, 3, 1):
        phase = "上京後" if day >= date(2027, 1, 11) else "Piscine準備"
        plans = [
            (
                f"{phase}：C演習20問",
                "Cの基礎問題を20問解き、コンパイル・実行・失敗原因を残す。",
                ["C小問20問の成功数", "コンパイルログ", "失敗原因と修正内容"],
                ["20問取り組んでいる", "15問以上成功、または失敗原因が全問ある"],
            ),
            (
                f"{phase}：アルゴリズム実装",
                "配列、文字列、探索、ソートのうち1テーマをCで実装する。",
                ["実装テーマ", "コード", "実行結果", "テストケース3件"],
                ["コードがコンパイルできる", "テストケース3件がある"],
            ),
            (
                f"{phase}：Gitレビュー練習",
                "Gitで小さな変更を3commitに分け、差分を説明する。",
                ["3commitのhash", "diffの説明", "GitHub URLまたはスクリーンショット"],
                ["3commitに分かれている", "差分の理由を説明している"],
            ),
            (
                f"{phase}：制限時間課題",
                "60分でCまたはシェルの小課題を1題解き、提出可能な形にする。",
                ["開始/終了時刻", "提出物", "できた点", "できなかった点"],
                ["60分の時間管理がある", "提出物が確認できる", "改善点がある"],
            ),
            (
                f"{phase}：説明・ピアレビュー準備",
                "今日のコードを人に説明する前提で、処理の流れと詰まりを整理する。",
                ["処理の流れ", "変数の変化", "詰まった点", "質問1つ"],
                ["処理の流れを第三者が追える", "質問が具体的である"],
            ),
            (
                f"{phase}：総合演習",
                "ターミナル操作、Git、C実装を1セットで行う。",
                ["ターミナル操作ログ", "Git commit", "Cコード", "実行結果"],
                ["1セット完了している", "コードと実行結果が確認できる"],
            ),
            (
                f"週次確認：{phase}耐性チェック",
                "1週間のコード量、成功数、失敗原因、生活負荷を確認する。",
                ["今週の演習数", "コンパイル成功数", "失敗原因トップ3", "翌週重点3つ"],
                ["数値で振り返れている", "翌週重点が具体的である"],
            ),
        ]
        title, description, deliverables, criteria = plans[weekday]
        return title, description, "assignment" if weekday < 6 else "review", deliverables, criteria, [
            "screenshot",
            "text",
            "github_url",
            "file",
        ]
    return (
        "日次学習・成果物提出",
        "その日の最優先課題に取り組み、成果物または実施証跡を残す。",
        "assignment",
        ["実施証跡", "未完了理由", "次の行動"],
        ["次にやることが日単位で決まっている"],
        ["screenshot", "photo", "text", "file", "github_url"],
    )


def _seed_empty_day_markers(session: Session, learner_id: uuid.UUID) -> int:
    existing_dates = set(
        session.execute(
            text(
                """
                SELECT DISTINCT scheduled_date
                FROM schedule_items
                WHERE learner_id = :learner_id
                  AND scheduled_date BETWEEN :start_date AND :end_date
                  AND schedule_key NOT LIKE 'taiga-%-daily-marker'
                """
            ),
            {"learner_id": learner_id, "start_date": SCHEDULE_START, "end_date": SCHEDULE_END},
        ).scalars()
    )
    count = 0
    day = SCHEDULE_START
    while day <= SCHEDULE_END:
        if day not in existing_dates:
            title, description, item_type, deliverables, criteria, evidence = _daily_marker_plan(day)
            _upsert_item(
                session,
                key=f"taiga-{day.isoformat()}-daily-marker",
                learner_id=learner_id,
                scheduled_date=day,
                title=title,
                description=description,
                item_type=item_type,
                priority=80,
                due_at=_due_at(day, "20:00") if item_type == "review" else _due_at(day, "23:59"),
                metadata={
                    "objective": description,
                    "deliverables": deliverables,
                    "acceptanceCriteria": criteria,
                    "allowedEvidenceTypes": evidence,
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
    session.execute(
        text(
            """
            DELETE FROM schedule_items
            WHERE schedule_key IN (
              'taiga-2026-09-07-42-web-test',
              'taiga-2026-09-04-42-web-test-retry'
            )
            """
        )
    )
    count += _seed_fixed_items(session, learner_id)
    count += _seed_pre_pc_days(session, learner_id)
    count += _seed_curriculum_assignments(session, learner_id)
    count += _seed_month_end_finance(session, learner_id)
    count += _seed_ranges(session, learner_id)
    count += _seed_empty_day_markers(session, learner_id)
    return count
