import { expect, test } from "@playwright/test";

const longTitle =
  "第十七週の長い日本語課題タイトル確認用テキストとSuperLongUnbrokenIdentifierABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
const assignmentId = "00000000-0000-0000-0000-000000000002";
const submissionId = "00000000-0000-0000-0000-000000000003";
const examId = "00000000-0000-0000-0000-000000000005";
const now = "2026-07-24T00:00:00Z";

async function mockApi(page: import("@playwright/test").Page, completedWeeks: number | null = 7) {
  await page.route("**/health", async (route) => {
    await route.fulfill({
      json: { status: "ok", app_env: "local", runner_enabled: false, exam_enabled: false },
    });
  });
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    const auth = route.request().headers().authorization ?? "Bearer local:taiga@example.local";
    const email = auth.replace("Bearer local:", "");
    const role = email.includes("admin") ? "admin" : email.includes("reviewer") ? "reviewer" : "learner";
    const displayName =
      role === "admin" ? "上山 捷馬 長い管理者名サンプル" : role === "reviewer" ? "Local Reviewer" : "上山 虎雅";

    if (path === "/api/v1/me") {
      await route.fulfill({
        json: {
          id: "00000000-0000-0000-0000-000000000011",
          displayName,
          role,
          status: "active",
          timezone: "Asia/Tokyo",
        },
      });
      return;
    }
    if (path === "/api/v1/dashboard") {
      await route.fulfill({
        json: {
          today: [{ id: assignmentId, stableCode: "TASK-017", title: longTitle, scheduledDate: "2026-07-24", status: "available" }],
          overdue: [],
          nextExam: { id: examId, stableCode: "EXAM-017", scheduledAt: now, status: "scheduled" },
          rank: "NOVA-長いランク名",
          capabilityGaps: ["設計説明の明確化", "長い技術識別子の扱い"],
        },
      });
      return;
    }
    if (path === "/api/v1/progress") {
      await route.fulfill({
        json: {
          completedWeeks,
          capabilities: [{ code: "long-content-readability-and-layout-stability", level: 2 }],
          rank: "NOVA-長いランク名",
        },
      });
      return;
    }
    if (path === "/api/v1/assignments") {
      await route.fulfill({
        json: {
          items: [
            { id: assignmentId, stableCode: "TASK-017", title: longTitle, scheduledDate: "2026-07-24", status: "available" },
            { id: "00000000-0000-0000-0000-000000000022", stableCode: "TASK-018", title: "短い課題", scheduledDate: "2026-07-25", status: "locked" },
          ],
          nextCursor: null,
        },
      });
      return;
    }
    if (path === `/api/v1/assignments/${assignmentId}`) {
      await route.fulfill({
        json: {
          assignment: { id: assignmentId, stableCode: "TASK-017", title: longTitle, scheduledDate: "2026-07-24", status: "available" },
          instructions: [
            "これは長い日本語本文とAPIClientGeneratedTypeNameWithoutBreakpoints0123456789を含む視覚QA用の説明です。",
          ],
          submissionSpec: {},
          submissions: [{ id: submissionId, assignmentId, version: 1, status: "needs_revision", createdAt: now }],
        },
      });
      return;
    }
    if (path === "/api/v1/reviews/queue") {
      await route.fulfill({
        json: {
          items: [{ id: submissionId, assignmentId, version: 1, status: "manual_review_pending", createdAt: now }],
          nextCursor: null,
        },
      });
      return;
    }
    if (path === "/api/v1/admin/users") {
      await route.fulfill({
        json: {
          items: [
            {
              id: "00000000-0000-0000-0000-000000000011",
              displayName: "上山 捷馬 長い管理者名サンプル",
              role: "admin",
              status: "active",
              timezone: "Asia/Tokyo",
            },
          ],
          nextCursor: null,
        },
      });
      return;
    }
    if (path === "/api/v1/admin/feature-flags") {
      await route.fulfill({
        json: { items: [{ key: "runner.enabled", enabled: false, version: 1 }, { key: "exam.enabled", enabled: false, version: 1 }] },
      });
      return;
    }
    if (path === "/api/v1/admin/analytics/learning") {
      await route.fulfill({
        json: { learners: 196, submissions: 392, approvedSubmissions: 280, examAttempts: 56, passedExamAttempts: 42 },
      });
      return;
    }
    if (path === "/api/v1/admin/curriculum/versions") {
      await route.fulfill({
        json: { items: [{ id: "00000000-0000-0000-0000-000000000099", version: "v4.0-local-mvp", status: "published", contentHash: "hash" }], nextCursor: null },
      });
      return;
    }
    if (path === "/api/v1/exams") {
      await route.fulfill({ json: { items: [], nextCursor: null } });
      return;
    }
    await route.fulfill({ status: 404, json: { error: path } });
  });
}

async function openVisualPage(
  page: import("@playwright/test").Page,
  path: string,
  options: { email?: string; completedWeeks?: number | null; width?: number; height?: number } = {},
) {
  await page.setViewportSize({ width: options.width ?? 1440, height: options.height ?? 900 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await mockApi(page, options.completedWeeks ?? 7);
  await page.goto(path);
  if (options.email) {
    await page.evaluate((email) => localStorage.setItem("taiga.localUser", email), options.email);
    await page.reload();
  }
  await expect(page.locator("#main-content")).toBeVisible();
  await page.waitForLoadState("networkidle");
  await page.evaluate(() => document.fonts.ready);
}

test.describe("TAIGA NOVA visual baselines", () => {
  test.skip(({ browserName }) => browserName !== "chromium", "Screenshot baselines are Chromium-only.");

  test("dashboard desktop and mobile are stable", async ({ page }) => {
    await openVisualPage(page, "/dashboard", { completedWeeks: 7 });
    await expect(page).toHaveScreenshot("dashboard-desktop.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/dashboard", { completedWeeks: 7, width: 375, height: 812 });
    await expect(page).toHaveScreenshot("dashboard-mobile.png", { fullPage: true, animations: "disabled" });
  });

  for (const [name, completedWeeks] of [
    ["ahead", 24],
    ["on-schedule", 7],
    ["behind", 0],
    ["unknown", null],
  ] as const) {
    test(`mission progress ${name} state is stable`, async ({ page }) => {
      await openVisualPage(page, "/dashboard", { completedWeeks });
      await expect(page.locator(".mission-card")).toHaveScreenshot(`mission-${name}.png`, {
        animations: "disabled",
      });
    });
  }

  test("core route screenshots are stable", async ({ page }) => {
    await openVisualPage(page, "/assignments");
    await expect(page).toHaveScreenshot("assignments-desktop-long-content.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/assignments", { width: 320, height: 800 });
    await expect(page).toHaveScreenshot("assignments-mobile-long-content.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/reviews", { email: "reviewer@example.local" });
    await expect(page).toHaveScreenshot("reviews-desktop.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/runner");
    await expect(page).toHaveScreenshot("runner-disabled.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/exams");
    await expect(page).toHaveScreenshot("exam-disabled.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/admin", { email: "admin@example.local" });
    await expect(page).toHaveScreenshot("admin-users.png", { fullPage: true, animations: "disabled" });
  });

  test("drawer, 404, and keyboard focus are stable", async ({ page }) => {
    await openVisualPage(page, "/dashboard", { width: 390, height: 844 });
    await page.getByRole("button", { name: "ナビゲーションを開く" }).click();
    await expect(page).toHaveScreenshot("mobile-drawer-open.png", { fullPage: true, animations: "disabled" });
    await page.keyboard.press("Escape");
    await expect(page.getByRole("button", { name: "ナビゲーションを開く" })).toBeFocused();
    await expect(page).toHaveScreenshot("drawer-focus-return.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/dashboard", { width: 390, height: 844 });
    await page.keyboard.press("Tab");
    await expect(page.getByRole("link", { name: "本文へスキップ" })).toBeFocused();
    await expect(page).toHaveScreenshot("keyboard-focus-skip-link.png", { fullPage: true, animations: "disabled" });
    await openVisualPage(page, "/off-orbit");
    await expect(page).toHaveScreenshot("off-orbit-404.png", { fullPage: true, animations: "disabled" });
  });
});
