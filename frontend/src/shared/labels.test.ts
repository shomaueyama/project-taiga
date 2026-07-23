import { describe, expect, it } from "vitest";

import { formatDate, labelForRole, labelForStatus, shortId } from "./labels";

describe("Japanese labels and formatting", () => {
  it("maps roles and statuses to shared Japanese labels", () => {
    expect(labelForRole("learner")).toBe("学習者");
    expect(labelForRole("reviewer")).toBe("レビュアー");
    expect(labelForRole("admin")).toBe("管理者");
    expect(labelForRole(undefined)).toBe("未認証");
    expect(labelForRole("mentor")).toBe("mentor");
    expect(labelForStatus("manual_review_pending")).toBe("レビュー待ち");
    expect(labelForStatus("security_rejected")).toBe("安全確認で停止");
    expect(labelForStatus(undefined)).toBe("未設定");
    expect(labelForStatus("custom_state")).toBe("custom_state");
  });

  it("formats dates and ids for user-facing UI", () => {
    expect(formatDate("2026-07-23")).toBe("2026/07/23");
    expect(formatDate(null)).toBe("日付未設定");
    expect(shortId("00000000-1111-2222-3333-444444444444")).toBe("00000000");
  });
});
