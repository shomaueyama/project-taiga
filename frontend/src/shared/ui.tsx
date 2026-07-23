import type { ReactNode } from "react";

import { labelForStatus } from "./labels";

export function StatusBadge({ status }: { status: string | null | undefined }) {
  return (
    <span className="status-badge" data-status={status ?? "unknown"}>
      {labelForStatus(status)}
    </span>
  );
}

export function LoadingState({ label = "読み込み中です" }: { label?: string }) {
  return (
    <p className="state-message" role="status" aria-live="polite">
      {label}
    </p>
  );
}

export function EmptyState({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="state-box">
      <p>{title}</p>
      {action}
    </div>
  );
}

export function Alert({
  tone = "info",
  children,
}: {
  tone?: "info" | "success" | "warning" | "danger";
  children: ReactNode;
}) {
  return (
    <div className={`alert alert-${tone}`} role={tone === "danger" ? "alert" : "status"}>
      {children}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  titleId,
}: {
  eyebrow: string;
  title: string;
  description: string;
  titleId?: string;
}) {
  return (
    <header className="page-header">
      <p className="eyebrow">{eyebrow}</p>
      <h1 id={titleId}>{title}</h1>
      <p className="summary">{description}</p>
    </header>
  );
}
