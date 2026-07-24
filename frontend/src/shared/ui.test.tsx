import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Alert, EmptyState, LoadingState, PageHeader, StatusBadge } from "./ui";

describe("shared UI states", () => {
  it("renders accessible state components", () => {
    render(
      <>
        <PageHeader
          eyebrow="確認"
          title="レビュー"
          titleId="review-title"
          description="提出物を確認します。"
        />
        <LoadingState />
        <EmptyState title="表示できる項目はありません。" action={<button type="button">戻る</button>} />
        <StatusBadge status={null} />
      </>,
    );

    expect(screen.getByRole("heading", { name: "レビュー" })).toHaveAttribute(
      "id",
      "review-title",
    );
    expect(screen.getByRole("status", { name: "" })).toHaveTextContent("読み込み中です");
    expect(screen.getByText("表示できる項目はありません。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "戻る" })).toBeInTheDocument();
    expect(screen.getByText("未設定")).toHaveAttribute("data-status", "unknown");
  });

  it("uses alert role only for danger messages", () => {
    render(
      <>
        <Alert>通常のお知らせ</Alert>
        <Alert tone="danger">処理に失敗しました。</Alert>
      </>,
    );

    expect(screen.getByRole("status")).toHaveTextContent("通常のお知らせ");
    expect(screen.getByRole("alert")).toHaveTextContent("処理に失敗しました。");
  });
});
