import { expect, test } from "@playwright/test";

const apiBaseUrl = "http://localhost:8000/api/v1";

test.describe.configure({ mode: "serial" });
test.skip(({ browserName }) => browserName !== "chromium", "Stateful Local MVP flows run in Chromium; cross-browser coverage lives in accessibility-responsive.spec.ts.");

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
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
  return errors;
}

async function createLearnerSubmission(request: import("@playwright/test").APIRequestContext) {
  const authHeaders = { Authorization: "Bearer local:taiga@example.local" };
  const assignments = await request.get(`${apiBaseUrl}/assignments`, { headers: authHeaders });
  expect(assignments.status()).toBe(200);
  const assignmentId = (await assignments.json()).items[0].id;
  const sha256 = "a".repeat(64);
  const upload = await request.post(`${apiBaseUrl}/uploads/presign`, {
    headers: { ...authHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {
      originalName: `answer-${crypto.randomUUID()}.md`,
      mediaType: "text/markdown",
      sizeBytes: 10,
      sha256,
    },
  });
  expect(upload.status()).toBe(201);
  const uploadId = (await upload.json()).id;
  const complete = await request.post(`${apiBaseUrl}/uploads/${uploadId}/complete`, {
    headers: { ...authHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: { sizeBytes: 10, sha256 },
  });
  expect(complete.status()).toBe(202);
  const submission = await request.post(`${apiBaseUrl}/assignments/${assignmentId}/submissions`, {
    headers: { ...authHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {
      sourceType: "file_upload",
      repositoryUrl: null,
      commitHash: null,
      uploadIds: [uploadId],
    },
  });
  expect(submission.status()).toBe(201);
  return { assignmentId, submissionId: (await submission.json()).id as string };
}

test("learner can view dashboard, assignments, disabled runner, and disabled exam", async ({
  page,
}) => {
  const errors = await openLocalMvp(page);
  await page.getByLabel("ローカル利用者").selectOption("taiga@example.local");

  await expect(page.getByText("上山 虎雅 · 学習者")).toBeVisible();
  await expect(page.getByRole("heading", { name: "ダッシュボード" })).toBeVisible();
  await page.getByRole("link", { name: "課題" }).click();
  await expect(page.getByRole("heading", { name: "課題" })).toBeVisible();
  await expect(page.getByLabel("課題詳細")).toContainText("提出履歴:");
  await page.getByRole("link", { name: "実行環境" }).click();
  await expect(page.getByRole("button", { name: "提出を実行確認する" })).toBeDisabled();
  await expect(page.getByText("実行結果はまだありません。")).toBeVisible();
  await page.getByRole("link", { name: "試験" }).click();
  await expect(page.getByRole("button", { name: "試験を開始" })).toBeDisabled();
  await expect(page.getByText("試験結果はまだありません。")).toBeVisible();
  expect(errors).toEqual([]);
});

test("learner can create a local demo submission and retain state on reload", async ({ page }) => {
  const errors = await openLocalMvp(page);
  await page.getByLabel("ローカル利用者").selectOption("taiga@example.local");
  await page.getByRole("link", { name: "課題" }).click();
  await page.getByRole("button", { name: "デモ回答を提出" }).click();
  await expect(page.getByText(/提出を作成しました:/)).toBeVisible();
  await expect(page.getByLabel("課題詳細")).toContainText("提出履歴:");
  await page.waitForLoadState("networkidle");

  await page.reload();
  await expect(page.getByText("上山 虎雅 · 学習者")).toBeVisible();
  await expect(page.getByRole("heading", { name: "課題" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("admin can view users, analytics, curriculum, flags, and review queue", async ({
  page,
  request,
}) => {
  const { submissionId } = await createLearnerSubmission(request);
  const errors = await openLocalMvp(page);
  await page.getByLabel("ローカル利用者").selectOption("admin@example.local");

  await expect(page.getByText("上山 捷馬 · 管理者")).toBeVisible();
  await page.getByRole("link", { name: "管理" }).click();
  await expect(page.getByRole("heading", { name: "管理" })).toBeVisible();
  await expect(page.getByLabel("機能フラグ")).toContainText("runner.enabled: 停止中");
  await expect(page.getByLabel("機能フラグ")).toContainText("exam.enabled: 停止中");
  await expect(page.getByText("公開済み")).toBeVisible();

  await page.getByRole("link", { name: "レビュー" }).click();
  await page.getByRole("button", { name: `${submissionId.slice(0, 8)}を承認` }).click();
  await expect(page.locator('[aria-live="polite"]').filter({ hasText: "承認済み" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("reviewer can request revision and admin can approve a resubmission", async ({
  page,
  request,
}) => {
  const firstSubmission = await createLearnerSubmission(request);
  const errors = await openLocalMvp(page);
  await page.getByLabel("ローカル利用者").selectOption("reviewer@example.local");

  await expect(page.getByText("Local Reviewer · レビュアー")).toBeVisible();
  await page.getByRole("link", { name: "レビュー" }).click();
  await page
    .getByRole("button", { name: `${firstSubmission.submissionId.slice(0, 8)}に修正依頼` })
    .click();
  await expect(page.locator('[aria-live="polite"]').filter({ hasText: "修正依頼" })).toBeVisible();

  const secondSubmission = await createLearnerSubmission(request);
  expect(secondSubmission.assignmentId).toBe(firstSubmission.assignmentId);

  await page.getByLabel("ローカル利用者").selectOption("admin@example.local");
  await expect(page.getByText("上山 捷馬 · 管理者")).toBeVisible();
  await page.getByRole("link", { name: "レビュー" }).click();
  await page
    .getByRole("button", { name: `${secondSubmission.submissionId.slice(0, 8)}を承認` })
    .click();
  await expect(page.locator('[aria-live="polite"]').filter({ hasText: "承認済み" })).toBeVisible();
  expect(errors).toEqual([]);
});

test("unknown local user receives 401 from the API", async ({ request }) => {
  const response = await request.get("http://localhost:8000/api/v1/me", {
    headers: { Authorization: "Bearer local:missing@example.local" },
  });
  expect(response.status()).toBe(401);
});

test("disabled runner and exam mutations fail without mutating via the API", async ({ request }) => {
  const authHeaders = { Authorization: "Bearer local:taiga@example.local" };
  const { submissionId } = await createLearnerSubmission(request);

  const runner = await request.post(`${apiBaseUrl}/submissions/${submissionId}/run`, {
    headers: { ...authHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: { reason: "e2e-disabled-contract" },
  });
  expect(runner.status()).toBe(403);
  expect(await runner.text()).not.toContain("traceback");

  const exams = await request.get(`${apiBaseUrl}/exams`, { headers: authHeaders });
  expect(exams.status()).toBe(200);
  const examId = (await exams.json()).items[0].id;
  const attempt = await request.post(`${apiBaseUrl}/exams/${examId}/attempts`, {
    headers: { ...authHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {},
  });
  expect(attempt.status()).toBe(403);
  expect(await attempt.text()).not.toContain("traceback");
});
