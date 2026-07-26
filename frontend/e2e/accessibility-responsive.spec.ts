import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const widths = [320, 375, 390, 768, 1024, 1440];

async function selectUser(page: import("@playwright/test").Page, email: string) {
  await page.evaluate((value) => window.localStorage.setItem("taiga.localUser", value), email);
  await page.getByLabel("ローカル利用者").selectOption(email);
}

async function expectNoHorizontalOverflow(page: import("@playwright/test").Page) {
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  expect(overflow).toBe(false);
}

test("major pages pass automated accessibility checks", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/dashboard");
  await selectUser(page, "taiga@example.local");
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
  await expect(page.locator(".sidebar").getByText("TAIGA NOVA")).toBeVisible();
  await expect(page.getByRole("progressbar", { name: "学習進捗" })).toBeVisible();
  let results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);

  await page.goto("/assignments");
  await expect(page.getByRole("heading", { name: "課題" })).toBeVisible();
  results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);

  await page.goto("/schedule");
  await expect(page.getByRole("heading", { name: "スケジュール" })).toBeVisible();
  results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);

  await selectUser(page, "reviewer@example.local");
  await page.goto("/reviews");
  await expect(page.getByRole("heading", { name: "レビュー" })).toBeVisible();
  results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);

  await selectUser(page, "admin@example.local");
  await page.goto("/admin");
  await expect(page.getByRole("heading", { name: "管理" })).toBeVisible();
  results = await new AxeBuilder({ page }).analyze();
  expect(results.violations).toEqual([]);
});

test("core routes are responsive without horizontal overflow", async ({ page }) => {
  for (const width of widths) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/dashboard");
    await selectUser(page, "taiga@example.local");
    await expectNoHorizontalOverflow(page);

    await page.goto("/assignments");
    await expect(page.getByRole("heading", { name: "課題" })).toBeVisible();
    await expectNoHorizontalOverflow(page);

    await page.goto("/schedule");
    await expect(page.getByRole("heading", { name: "スケジュール" })).toBeVisible();
    await expectNoHorizontalOverflow(page);

    await selectUser(page, "reviewer@example.local");
    await page.goto("/reviews");
    await expect(page.getByRole("heading", { name: "レビュー" })).toBeVisible();
    await expectNoHorizontalOverflow(page);

    await selectUser(page, "admin@example.local");
    await page.goto("/admin");
    await expect(page.getByRole("heading", { name: "管理" })).toBeVisible();
    await expectNoHorizontalOverflow(page);
  }
});

test("keyboard user can skip to content and activate navigation", async ({ page, browserName }) => {
  await page.goto("/");
  if (browserName === "webkit") {
    await page.getByRole("link", { name: "本文へスキップ" }).focus();
  } else {
    await page.keyboard.press("Tab");
  }
  await expect(page.getByRole("link", { name: "本文へスキップ" })).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#main-content")).toBeFocused();

  await page.getByRole("link", { name: "課題" }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "課題" })).toBeVisible();
  await expect(page.locator("#main-content")).toBeFocused();
});

test("dashboard initial load does not issue duplicate API requests", async ({ page }) => {
  const counts = new Map<string, number>();
  await page.addInitScript(() => {
    window.localStorage.setItem("taiga.localUser", "taiga@example.local");
  });
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.origin !== "http://localhost:8000") {
      return;
    }
    counts.set(url.pathname, (counts.get(url.pathname) ?? 0) + 1);
  });

  await page.goto("/dashboard");
  await selectUser(page, "taiga@example.local");
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
  await expect(page.getByText("上山 虎雅 · 学習者")).toBeVisible();
  await page.waitForLoadState("networkidle");

  expect(counts.get("/api/health")).toBe(1);
  expect(counts.get("/api/v1/me")).toBe(1);
  expect(counts.get("/api/v1/dashboard")).toBe(1);
  expect(counts.get("/api/v1/assignments")).toBe(1);
  expect(counts.get("/api/v1/progress")).toBe(1);
});
