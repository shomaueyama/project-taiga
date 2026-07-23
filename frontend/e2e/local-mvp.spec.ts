import { expect, test } from "@playwright/test";

async function watchPage(page: import("@playwright/test").Page) {
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(`console.error: ${message.text()}`);
    }
  });
  page.on("requestfailed", (request) => {
    errors.push(`requestfailed: ${request.url()} ${request.failure()?.errorText}`);
  });
  page.on("response", (response) => {
    if (response.status() >= 500) {
      errors.push(`http ${response.status()}: ${response.url()}`);
    }
  });
  return errors;
}

async function openLocalMvp(page: import("@playwright/test").Page) {
  const errors = await watchPage(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Project Taiga" })).toBeVisible();
  return errors;
}

test("learner can view dashboard, assignments, disabled runner, and disabled exam", async ({
  page,
}) => {
  const errors = await openLocalMvp(page);
  await page.getByLabel("Local user").selectOption("taiga@example.local");

  await expect(page.getByText("上山 虎雅 · learner")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Assignments" })).toBeVisible();
  await expect(page.getByLabel("Assignment detail")).toContainText("Submissions:");
  await expect(page.getByRole("button", { name: "Run submission" })).toBeDisabled();
  await expect(page.getByText("Runner disabled locally")).toBeVisible();
  await expect(page.getByRole("button", { name: "Start exam" })).toBeDisabled();
  await expect(page.getByText("Exam disabled locally")).toBeVisible();
  await expect(page.getByText("Admin role required")).toBeVisible();
  expect(errors).toEqual([]);
});

test("learner can create a local demo submission and retain state on reload", async ({ page }) => {
  const errors = await openLocalMvp(page);
  await page.getByLabel("Local user").selectOption("taiga@example.local");
  await page.getByRole("button", { name: "Submit demo answer" }).click();
  await expect(page.getByText(/Submission created:/)).toBeVisible();
  await expect(page.getByLabel("Assignment detail")).toContainText("Submissions:");
  await page.waitForLoadState("networkidle");

  await page.reload();
  await expect(page.getByText("上山 虎雅 · learner")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Assignments" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("admin can view users, analytics, curriculum, flags, and review queue", async ({ page }) => {
  const errors = await openLocalMvp(page);
  await page.getByLabel("Local user").selectOption("admin@example.local");

  await expect(page.getByText("上山 捷馬 · admin")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Admin" })).toBeVisible();
  await expect(page.getByLabel("Feature flags")).toContainText("runner.enabled: disabled");
  await expect(page.getByLabel("Feature flags")).toContainText("exam.enabled: disabled");
  await expect(page.getByText("published")).toBeVisible();

  const approveButton = page.getByRole("button", { name: "Approve" });
  if (await approveButton.isEnabled()) {
    await approveButton.click();
    await expect(page.getByText("approved")).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("unknown local user receives 401 from the API", async ({ request }) => {
  const response = await request.get("http://localhost:8000/api/v1/me", {
    headers: { Authorization: "Bearer local:missing@example.local" },
  });
  expect(response.status()).toBe(401);
});
