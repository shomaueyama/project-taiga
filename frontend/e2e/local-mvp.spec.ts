import { expect, test } from "@playwright/test";

const apiBaseUrl = "http://localhost:8000/api/v1";

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

test("admin can view users, analytics, curriculum, flags, and review queue", async ({
  page,
  request,
}) => {
  const { submissionId } = await createLearnerSubmission(request);
  const errors = await openLocalMvp(page);
  await page.getByLabel("Local user").selectOption("admin@example.local");

  await expect(page.getByText("上山 捷馬 · admin")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Admin" })).toBeVisible();
  await expect(page.getByLabel("Feature flags")).toContainText("runner.enabled: disabled");
  await expect(page.getByLabel("Feature flags")).toContainText("exam.enabled: disabled");
  await expect(page.getByText("published")).toBeVisible();

  await page.getByRole("button", { name: `Approve ${submissionId.slice(0, 8)}` }).click();
  await expect(page.getByText("approved")).toBeVisible();
  expect(errors).toEqual([]);
});

test("reviewer can request revision and admin can approve a resubmission", async ({
  page,
  request,
}) => {
  const firstSubmission = await createLearnerSubmission(request);
  const errors = await openLocalMvp(page);
  await page.getByLabel("Local user").selectOption("reviewer@example.local");

  await expect(page.getByText("Local Reviewer · reviewer")).toBeVisible();
  await page
    .getByRole("button", { name: `Request revision ${firstSubmission.submissionId.slice(0, 8)}` })
    .click();
  await expect(page.getByText("needs_revision")).toBeVisible();

  const secondSubmission = await createLearnerSubmission(request);
  expect(secondSubmission.assignmentId).toBe(firstSubmission.assignmentId);

  await page.getByLabel("Local user").selectOption("admin@example.local");
  await expect(page.getByText("上山 捷馬 · admin")).toBeVisible();
  await page
    .getByRole("button", { name: `Approve ${secondSubmission.submissionId.slice(0, 8)}` })
    .click();
  await expect(page.getByText("approved")).toBeVisible();
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
