# 概要

Project Taiga Local MVP に、課題ページとは独立した `/schedule` スケジュール・カレンダー機能を追加した。

学習者 Taiga と管理者 Shoma の初期運用を前提に、日単位の予定、課題、重要イベント、遅延、レビュー待ち、Piscine開始までの残日数を確認できる。

# 変更ファイル

- `backend/alembic/versions/0003_schedule_calendar.py`
- `backend/src/taiga/api_schemas.py`
- `backend/src/taiga/database_schema.py`
- `backend/src/taiga/main.py`
- `backend/src/taiga/schedule_domain.py`
- `backend/src/taiga/schedule_service.py`
- `backend/src/taiga/schedule_seed.py`
- `backend/src/taiga/seed_data/schedule/fixed_items.json`
- `backend/src/taiga/curriculum_seed.py`
- `backend/src/taiga/production_seed.py`
- `backend/tests/test_schedule_calendar.py`
- `backend/tests/test_production_seed.py`
- `frontend/src/shared/api/client.ts`
- `frontend/src/shared/labels.ts`
- `frontend/src/routes/App.tsx`
- `frontend/src/routes/App.test.tsx`
- `frontend/src/styles.css`
- `frontend/e2e/accessibility-responsive.spec.ts`
- `frontend/e2e/local-mvp.spec.ts`
- `frontend/e2e/visual-regression.spec.ts-snapshots/*.png`

# DB変更

`schedule_items` テーブルを追加した。

主な列:

- `schedule_key`
- `learner_id`
- `scheduled_date`
- `start_at`
- `end_at`
- `title`
- `description`
- `item_type`
- `assignment_id`
- `milestone_key`
- `status_override`
- `priority`
- `due_at`
- `source_url`
- `is_required`
- `metadata_json`

# API

追加API:

- `GET /api/v1/schedule?from=YYYY-MM-DD&to=YYYY-MM-DD`
- `GET /api/v1/schedule/{selectedDate}`
- `GET /api/v1/schedule/summary`
- `POST /api/v1/admin/schedule/seed`
- `POST /api/v1/admin/schedule-items`
- `PATCH /api/v1/admin/schedule-items/{scheduleItemId}`
- `DELETE /api/v1/admin/schedule-items/{scheduleItemId}`

状態計算は `schedule_domain.py` に集約し、APIは `displayStatus`, `isOverdue`, `overdueDays`, `isToday`, `assignmentUrl` を返す。

# UI

- サイドバーに「スケジュール」を追加
- `/schedule` に月曜始まりの月カレンダーを追加
- 前月、次月、今日へ戻る操作を追加
- 今日、選択日、件数、代表状態、重要日程を表示
- 日別詳細パネルに成果物、合格条件、許可証跡、期限、遅延日数、根拠URL、課題詳細リンクを表示
- 管理者は予定の追加、編集、キャンセル、削除が可能
- 320px幅で横スクロールなしを確認

# seedデータ範囲

`2026-07-27` から `2027-03-26` まで、日付ごとに最低1件のschedule itemを投入する。

seedは `schedule_key` で冪等にupsertする。固定データはJSONに分離し、既存カリキュラム課題は `task_assignments` からschedule itemへ接続する。

# 重要日程

登録済み:

- `2026-08-16` PC購入予定日
- `2026-09-05` 42 Tokyo高校生向けオープンスクール・現地見学
- `2026-09-05` 正式Introduction Meeting扱いか確認
- `2026-09-06` Vaundyライブ
- `2026-09-30` 正式Introduction Meeting第一候補
- `2026-10-03` 基本情報技術者試験
- `2026-11-01` 本格的な部屋探し開始
- `2026-12-01` オンライン内見・候補絞り込み開始
- `2026-12-15` 契約判断の内部期限
- `2026-12-31` 推奨貯金60万円の確認期限
- `2027-01-04` から `2027-01-10` 上京・入居候補期間
- `2027-01-11` 東京生活・通学確認開始
- `2027-02-01` 模擬Piscine強化期間開始
- `2027-02-22` 本番直前調整開始
- `2027-02-28` 前日準備・休養
- `2027-03-01` から `2027-03-26` Piscine本番
- `2027-04-02` 合格発表
- `2027-04-14` 春入学式

9月5日のオープンスクールと9月30日の正式Introduction Meeting候補は別イベントとして保持している。

# 遅延判定

`due_at` を現在時刻が過ぎ、かつ `approved` / `cancelled` でない場合に期限超過とする。

- 未提出・進行中・修正依頼中の期限超過: `learner_overdue`
- 提出済みレビュー待ちの期限超過: `review_overdue`
- 承認済み: 期限超過でも遅延にしない

遅延日数はJSTの日付差で算出する。

# テスト結果

- `make lint`: 成功
- `make typecheck`: 成功
- `make test`: 成功、backend 75 passed / frontend 19 passed
- `make test-e2e`: 成功、27 passed / 36 skipped
- 手動API確認:
  - `/api/v1/schedule?from=2026-07-27&to=2026-08-02`
  - `/api/v1/schedule/summary`
- 手動画面確認:
  - `http://localhost:5173/schedule`
  - desktop `1280x900`
  - mobile `320x900` full-page

# 手動確認結果

Docker Compose上でbackend/frontendを再ビルドし、migrationとseedを実行した。

```text
make migrate
make seed
make seed
docker compose up -d backend frontend worker
```

`/schedule` で月カレンダー、概要、日別詳細、課題詳細リンク、320px表示を確認した。

# 未解決事項

- 8月3日以降の細かい教材章立ては、既存カリキュラム課題と汎用の日次マーカーで構成している。指定教材が追加された場合はseedデータを増やす余地がある。

# 自己レビュー1回目

1. 目的適合性: 1.0
2. 課題ページとの責務分離: 1.0
3. 日単位データの具体性: 0.9
4. 遅延ロジックの正確性: 1.0
5. 成果物中心の運用: 0.95
6. 既存設計との整合性: 1.0
7. UI・レスポンシブ・アクセシビリティ: 0.95
8. テストの十分性: 0.95
9. データ・日程の根拠と誤認防止: 0.95
10. ローカルでの再現性・保守性: 1.0

合計: 9.7 / 10

# 修正内容

- schedule queryを `/schedule` 表示時だけ有効化し、他ページの余計なAPI呼び出しを抑制した。
- モバイルの最優先表示が細く潰れないようCSSを修正した。
- E2Eへスケジュール画面、アクセシビリティ、レスポンシブ確認を追加した。
- サイドバー追加に伴うビジュアルスナップショットを更新した。
- 管理者向けの予定追加・編集・キャンセル・削除APIとUIを追加した。
- 本番seedでもTaiga learnerにスケジュールを投入するようにした。
- 管理者表示時に本番のTaiga learnerを確実に対象にするよう修正した。

# 自己レビュー2回目以降

再実行結果:

- `make lint`: 成功
- `make typecheck`: 成功
- `make test`: 成功、backend 75 passed / frontend 19 passed
- `make test-e2e`: 成功、27 passed / 36 skipped

合計: 9.85 / 10

# 最終得点

9.85 / 10
