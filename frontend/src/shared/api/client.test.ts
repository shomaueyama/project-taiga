import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  apiErrorMessage,
  createDemoSubmission,
  createExamAttempt,
  deleteSubmission,
  getAdminUsers,
  getAnalytics,
  getAssignment,
  getAssignments,
  getCurriculumVersions,
  getDashboard,
  getExams,
  getFeatureFlags,
  getHealth,
  getMe,
  getProgress,
  getReviewQueue,
  getReviewSubmissions,
  getStoredLocalUser,
  reviewSubmission,
  runSubmission,
  setStoredLocalUser,
  startExamAttempt,
  submitExamAttempt,
} from "./client";

const uuid1 = "00000000-0000-0000-0000-000000000001";
const uuid2 = "00000000-0000-0000-0000-000000000002";
const uuid3 = "00000000-0000-0000-0000-000000000003";
const now = "2026-07-23T00:00:00Z";

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

describe("api client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it("persists the selected local user and sends local auth headers", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      expect(String(input)).toBe("http://localhost:8000/api/v1/me");
      expect(init?.headers).toMatchObject({ Authorization: "Bearer local:reviewer@example.local" });
      return jsonResponse({
        id: uuid1,
        displayName: "Reviewer",
        role: "reviewer",
        status: "active",
        timezone: "Asia/Tokyo",
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    expect(getStoredLocalUser()).toBe("taiga@example.local");
    setStoredLocalUser("reviewer@example.local");
    expect(getStoredLocalUser()).toBe("reviewer@example.local");
    await expect(getMe()).resolves.toMatchObject({ role: "reviewer" });
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("parses read endpoints and rejects non-2xx responses", async () => {
    const responses: Record<string, unknown> = {
      "/api/health": { status: "ok", app_env: "local", runner_enabled: false, exam_enabled: true },
      "/api/v1/dashboard": { today: [], overdue: [], nextExam: null, rank: null, capabilityGaps: [] },
      "/api/v1/assignments": {
        items: [
          {
            id: uuid1,
            stableCode: "TASK-001",
            title: "Task",
            scheduledDate: "2026-07-23",
            status: "available",
          },
        ],
        nextCursor: null,
      },
      [`/api/v1/assignments/${uuid1}`]: {
        assignment: {
          id: uuid1,
          stableCode: "TASK-001",
          title: "Task",
          scheduledDate: "2026-07-23",
          status: "available",
        },
        instructions: ["Read"],
        submissionSpec: { kind: "markdown" },
        submissions: [],
      },
      "/api/v1/progress": { completedWeeks: 1, capabilities: [{ code: "c", level: 2 }], rank: "C" },
      "/api/v1/reviews/queue": {
        items: [{ id: uuid2, assignmentId: uuid1, version: 1, status: "manual_review_pending", createdAt: now }],
        nextCursor: null,
      },
      "/api/v1/exams": {
        items: [{ id: uuid3, stableCode: "EXAM-001", title: "Exam", scheduledAt: now }],
        nextCursor: null,
      },
      "/api/v1/admin/users": {
        items: [
          { id: uuid1, displayName: "Admin", role: "admin", status: "active", timezone: "Asia/Tokyo" },
        ],
        nextCursor: null,
      },
      "/api/v1/admin/feature-flags": { items: [{ key: "runner.enabled", enabled: false, version: 1 }] },
      "/api/v1/admin/analytics/learning": {
        learners: 1,
        submissions: 2,
        approvedSubmissions: 1,
        examAttempts: 0,
        passedExamAttempts: 0,
      },
      "/api/v1/admin/curriculum/versions": {
        items: [{ id: uuid1, version: "v4.0", status: "published", contentHash: "abc" }],
        nextCursor: null,
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = new URL(String(input));
        const path = url.pathname;
        if (path === "/api/v1/missing") {
          return jsonResponse({ error: "missing" }, 404);
        }
        if (path === "/api/v1/reviews/queue" && url.searchParams.get("status_filter") === "all") {
          return jsonResponse({
            items: [
              {
                id: uuid2,
                assignmentId: uuid1,
                assignmentTitle: "Task",
                assignmentStableCode: "TASK-001",
                learnerName: "Learner",
                version: 1,
                status: "approved",
                createdAt: now,
              },
            ],
            nextCursor: null,
          });
        }
        return jsonResponse(responses[path]);
      }),
    );

    await expect(getHealth()).resolves.toMatchObject({ exam_enabled: true });
    await expect(getDashboard()).resolves.toMatchObject({ today: [] });
    await expect(getAssignments()).resolves.toMatchObject({ items: [{ stableCode: "TASK-001" }] });
    await expect(getAssignment(uuid1)).resolves.toMatchObject({ instructions: ["Read"] });
    await expect(getProgress()).resolves.toMatchObject({ completedWeeks: 1 });
    await expect(getReviewQueue()).resolves.toMatchObject({ items: [{ status: "manual_review_pending" }] });
    await expect(getReviewSubmissions()).resolves.toMatchObject({ items: [{ assignmentTitle: "Task" }] });
    await expect(getExams()).resolves.toMatchObject({ items: [{ stableCode: "EXAM-001" }] });
    await expect(getAdminUsers()).resolves.toMatchObject({ items: [{ role: "admin" }] });
    await expect(getFeatureFlags()).resolves.toMatchObject({ items: [{ key: "runner.enabled" }] });
    await expect(getAnalytics()).resolves.toMatchObject({ approvedSubmissions: 1 });
    await expect(getCurriculumVersions()).resolves.toMatchObject({ items: [{ version: "v4.0" }] });
  });

  it("sends idempotency keys and request bodies for mutation workflows", async () => {
    const calls: Array<{ path: string; body: unknown; key: string | null }> = [];
    vi.stubGlobal("crypto", { randomUUID: vi.fn(() => "idempotency-key") });
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = new URL(String(input)).pathname;
        calls.push({
          path,
          body: init?.body ? JSON.parse(String(init.body)) : null,
          key: new Headers(init?.headers).get("Idempotency-Key"),
        });
        if (path === "/api/v1/uploads/presign") {
          return jsonResponse({ id: uuid1, status: "created", uploadUrl: "file://upload", expiresAt: now }, 201);
        }
        if (path === `/api/v1/uploads/${uuid1}/complete`) {
          return jsonResponse({ id: uuid1, status: "accepted", expiresAt: now }, 202);
        }
        if (path === `/api/v1/assignments/${uuid2}/submissions`) {
          return jsonResponse({ id: uuid3, assignmentId: uuid2, version: 1, status: "manual_review_pending", createdAt: now }, 201);
        }
        if (path === `/api/v1/submissions/${uuid3}/run`) {
          return jsonResponse({ id: uuid1, submissionId: uuid3, status: "succeeded", attempt: 1, sanitizedResult: { passed: true } }, 201);
        }
        if (path === `/api/v1/submissions/${uuid3}/reviews`) {
          return jsonResponse({ id: uuid1, result: "approved", comment: "ok", createdAt: now }, 201);
        }
        if (path === `/api/v1/submissions/${uuid3}` && init?.method === "DELETE") {
          return jsonResponse(null, 204);
        }
        if (path === `/api/v1/exams/${uuid2}/attempts`) {
          return jsonResponse({ id: uuid1, examId: uuid2, status: "reserved", attemptNumber: 1 }, 201);
        }
        if (path === `/api/v1/exam-attempts/${uuid1}/start`) {
          return jsonResponse({
            attempt: { id: uuid1, examId: uuid2, status: "in_progress", attemptNumber: 1 },
            variantSnapshot: {},
            startsAt: now,
            deadlineAt: now,
            submittedAt: null,
            result: null,
          });
        }
        if (path === `/api/v1/exam-attempts/${uuid1}/submit`) {
          return jsonResponse({
            attempt: { id: uuid1, examId: uuid2, status: "oral_pending", attemptNumber: 1 },
            variantSnapshot: {},
            startsAt: now,
            deadlineAt: now,
            submittedAt: now,
            result: { score: 80 },
          });
        }
        return jsonResponse({ error: "unexpected" }, 500);
      }),
    );

    await expect(createDemoSubmission(uuid2)).resolves.toMatchObject({ id: uuid3, version: 1 });
    await expect(runSubmission(uuid3)).resolves.toMatchObject({ status: "succeeded" });
    await expect(reviewSubmission(uuid3, "approved")).resolves.toMatchObject({ result: "approved" });
    await expect(deleteSubmission(uuid3)).resolves.toBeUndefined();
    await expect(createExamAttempt(uuid2)).resolves.toMatchObject({ status: "reserved" });
    await expect(startExamAttempt(uuid1)).resolves.toMatchObject({ attempt: { status: "in_progress" } });
    await expect(submitExamAttempt(uuid1)).resolves.toMatchObject({ attempt: { status: "oral_pending" } });

    expect(calls.every((call) => call.key === "idempotency-key")).toBe(true);
    expect(calls.map((call) => call.path)).toContain(`/api/v1/submissions/${uuid3}/reviews`);
    expect(calls.map((call) => call.path)).toContain(`/api/v1/submissions/${uuid3}`);
    expect(calls.find((call) => call.path.endsWith("/reviews"))?.body).toMatchObject({
      result: "approved",
    });
  });

  it("raises useful errors for failed health and API requests", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) =>
        String(input).endsWith("/api/health")
          ? jsonResponse({ status: "down" }, 503)
          : jsonResponse({ error: "denied" }, 403),
      ),
    );

    await expect(getHealth()).rejects.toThrow("Health check failed: 503");
    await expect(getAssignments()).rejects.toThrow("API request failed: 403");
  });

  it("maps production access and cold-start errors to Japanese messages", () => {
    expect(apiErrorMessage(new ApiError("timeout", 0))).toContain("起動");
    expect(apiErrorMessage(new ApiError("unauthorized", 401))).toContain("パスワード");
    expect(apiErrorMessage(new ApiError("forbidden", 403))).toContain("アクセス権");
    expect(apiErrorMessage(new ApiError("server", 503))).toContain("サーバー");
  });
});
