export const roleLabels: Record<string, string> = {
  learner: "学習者",
  reviewer: "レビュアー",
  admin: "管理者",
};

export const statusLabels: Record<string, string> = {
  ok: "正常",
  enabled: "有効",
  disabled: "停止中",
  available: "対応可能",
  not_started: "未着手",
  in_progress: "進行中",
  awaiting_submission: "提出待ち",
  completed: "完了",
  missed: "未対応",
  submitted: "提出済み",
  queued: "待機中",
  running: "実行中",
  manual_review_pending: "レビュー待ち",
  needs_revision: "修正依頼",
  approved: "承認済み",
  succeeded: "完了",
  failed: "失敗",
  timed_out: "時間切れ",
  security_rejected: "安全確認で停止",
  ready: "準備完了",
  reserved: "予約済み",
  oral_pending: "口頭確認待ち",
  passed: "合格",
  expired: "期限切れ",
  published: "公開済み",
  restricted: "権限が必要",
};

export function labelForStatus(status: string | null | undefined): string {
  if (!status) {
    return "未設定";
  }
  return statusLabels[status] ?? status;
}

export function labelForRole(role: string | null | undefined): string {
  if (!role) {
    return "未認証";
  }
  return roleLabels[role] ?? role;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "日付未設定";
  }
  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Tokyo",
  }).format(new Date(value));
}

export function shortId(id: string): string {
  return id.slice(0, 8);
}
