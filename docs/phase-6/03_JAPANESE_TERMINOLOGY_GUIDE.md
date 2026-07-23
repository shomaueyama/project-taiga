# Japanese Terminology Guide

| Concept | Japanese | Notes |
|---|---|---|
| assignment | 課題 | Use for task assignment visible to learner |
| submission | 提出 | Use for submitted work and submission actions |
| resubmission | 再提出 | Use when revision flow is explicit |
| review | レビュー | Domain term retained for reviewer workflow |
| approve | 承認 | Use for positive review result |
| reject / needs revision | 修正依頼 | Avoid harsh "却下" for learner-facing review feedback |
| reviewer | レビュアー | Role label |
| learner | 学習者 | Role label |
| admin | 管理者 | Role label |
| exam | 試験 | Server-authoritative exam flow |
| oral review | 口頭確認 | Use for oral pending state |
| runner | 実行確認 | User-facing label for local runner workflow |
| queued | 待機中 | Job state |
| in progress | 進行中 | General active state |
| completed / succeeded | 完了 | Successful completion |
| failed | 失敗 | Non-security failure |
| expired | 期限切れ | Deadline or validity expiration |
| security rejected | 安全確認で停止 | Avoid leaking internal security detail |
| feature disabled | 停止中 | Pair with explanatory text |

## Formatting

- Dates use `ja-JP` formatting through `formatDate`.
- Internal enum values stay English in API and persistence layers.
- User-facing status and role labels are centralized in `frontend/src/shared/labels.ts`.
