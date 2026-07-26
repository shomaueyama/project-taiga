import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

const assignmentId = "00000000-0000-0000-0000-000000000002";
const submissionId = "00000000-0000-0000-0000-000000000003";
const reviewId = "00000000-0000-0000-0000-000000000004";
const examId = "00000000-0000-0000-0000-000000000005";
const attemptId = "00000000-0000-0000-0000-000000000006";
const now = "2026-07-23T00:00:00Z";

function response(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}

function userForEmail(email: string) {
  if (email === "admin@example.local") {
    return {
      id: "00000000-0000-0000-0000-000000000011",
      displayName: "上山 捷馬",
      role: "admin",
      status: "active",
      timezone: "Asia/Tokyo",
    };
  }
  if (email === "reviewer@example.local") {
    return {
      id: "00000000-0000-0000-0000-000000000012",
      displayName: "Local Reviewer",
      role: "reviewer",
      status: "active",
      timezone: "Asia/Tokyo",
    };
  }
  return {
    id: "00000000-0000-0000-0000-000000000013",
    displayName: "上山 虎雅",
    role: "learner",
    status: "active",
    timezone: "Asia/Tokyo",
  };
}

function localUserFrom(init?: RequestInit) {
  const authorization = new Headers(init?.headers).get("Authorization") ?? "";
  return authorization.replace("Bearer local:", "");
}

function installFetch(
  options: {
    runnerEnabled?: boolean;
    examEnabled?: boolean;
    appEnv?: string;
    requireLogin?: boolean;
    todayAssignment?: boolean;
    completedWeeks?: number | null;
  } = {},
) {
  const calls: Array<{ path: string; method: string; body: unknown }> = [];
  let loggedIn = !options.requireLogin;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input));
    const path = url.pathname;
    const method = init?.method ?? "GET";
    const body = init?.body ? JSON.parse(String(init.body)) : null;
    calls.push({ path, method, body });

    if (path === "/api/health") {
      return response({
        status: "ok",
        app_env: options.appEnv ?? "local",
        runner_enabled: options.runnerEnabled ?? false,
        exam_enabled: options.examEnabled ?? false,
      });
    }
    if (path === "/api/v1/me") {
      if (!loggedIn) {
        return response({ detail: "Authentication required" }, 401);
      }
      return response(userForEmail(localUserFrom(init)));
    }
    if (path === "/api/v1/auth/login") {
      loggedIn = true;
      return response(userForEmail(String(body?.email ?? "admin@example.local")));
    }
    if (path === "/api/v1/auth/logout") {
      loggedIn = false;
      return response({ status: "ok" });
    }
    if (path === "/api/v1/dashboard") {
      const today = options.todayAssignment
        ? [
            {
              id: assignmentId,
              stableCode: "TASK-001",
              title: "Typing basics",
              scheduledDate: "2026-07-23",
              status: "available",
            },
          ]
        : [];
      return response({
        today,
        overdue: [],
        nextExam: options.examEnabled
          ? { id: examId, stableCode: "EXAM-001", scheduledAt: now, status: "scheduled" }
          : null,
        rank: null,
        capabilityGaps: [],
      });
    }
    if (path === "/api/v1/assignments") {
      return response({
        items: [
          {
            id: assignmentId,
            stableCode: "TASK-001",
            title: "Typing basics",
            scheduledDate: "2026-07-23",
            status: "available",
          },
        ],
        nextCursor: null,
      });
    }
    if (path === "/api/v1/schedule") {
      return response({
        fromDate: url.searchParams.get("from"),
        toDate: url.searchParams.get("to"),
        days: [
          {
            date: "2026-07-27",
            representativeStatus: "learner_overdue",
            isToday: false,
            items: [
              {
                id: "00000000-0000-0000-0000-000000000021",
                scheduleKey: "taiga-2026-07-27-fe-baseline",
                date: "2026-07-27",
                startAt: null,
                endAt: null,
                title: "基本情報：現在地確認",
                description: "現在地確認を提出する。",
                itemType: "assignment",
                assignmentId,
                milestoneKey: null,
                priority: 10,
                dueAt: "2026-07-27T14:59:00Z",
                sourceUrl: null,
                isRequired: true,
                displayStatus: "learner_overdue",
                isOverdue: true,
                overdueDays: 1,
                isToday: false,
                assignmentUrl: `/assignments/${assignmentId}`,
                metadata: {
                  deliverables: ["回答画面"],
                  acceptanceCriteria: ["Shomaが承認"],
                  allowedEvidenceTypes: ["screenshot", "photo", "text"],
                },
              },
            ],
          },
        ],
      });
    }
    if (path === "/api/v1/schedule/summary") {
      return response({
        todayCount: 1,
        learnerOverdueCount: 1,
        reviewWaitingCount: 0,
        nextImportantDate: "2026-09-05",
        nextImportantTitle: "42 Tokyo高校生向けオープンスクール・現地見学",
        daysUntilPiscine: 218,
      });
    }
    if (path.startsWith("/api/v1/schedule/")) {
      return response({
        date: path.split("/").at(-1) ?? "2026-07-27",
        representativeStatus: "learner_overdue",
        isToday: false,
        items: [
          {
            id: "00000000-0000-0000-0000-000000000021",
            scheduleKey: "taiga-2026-07-27-fe-baseline",
            date: "2026-07-27",
            startAt: null,
            endAt: null,
            title: "基本情報：現在地確認",
            description: "現在地確認を提出する。",
            itemType: "assignment",
            assignmentId,
            milestoneKey: null,
            priority: 10,
            dueAt: "2026-07-27T14:59:00Z",
            sourceUrl: null,
            isRequired: true,
            displayStatus: "learner_overdue",
            isOverdue: true,
            overdueDays: 1,
            isToday: false,
            assignmentUrl: `/assignments/${assignmentId}`,
            metadata: {
              deliverables: ["回答画面"],
              acceptanceCriteria: ["Shomaが承認"],
              allowedEvidenceTypes: ["screenshot", "photo", "text"],
            },
          },
        ],
      });
    }
    if (path === `/api/v1/assignments/${assignmentId}` && method === "GET") {
      return response({
        assignment: {
          id: assignmentId,
          stableCode: "TASK-001",
          title: "Typing basics",
          scheduledDate: "2026-07-23",
          status: "available",
        },
        instructions: ["Submit a short answer."],
        submissionSpec: {},
        submissions: [],
      });
    }
    if (path === `/api/v1/assignments/${assignmentId}/submissions`) {
      return response({
        id: submissionId,
        assignmentId,
        version: 1,
        status: "manual_review_pending",
        createdAt: now,
      }, 201);
    }
    if (path === "/api/v1/uploads/presign") {
      return response({ id: reviewId, status: "created", uploadUrl: "file://upload", expiresAt: now }, 201);
    }
    if (path === `/api/v1/uploads/${reviewId}/complete`) {
      return response({ id: reviewId, status: "accepted", expiresAt: now }, 202);
    }
    if (path === "/api/v1/progress") {
      return response({ completedWeeks: options.completedWeeks ?? 0, capabilities: [], rank: null });
    }
    if (path === "/api/v1/reviews/queue") {
      return response({
        items: [{ id: submissionId, assignmentId, version: 1, status: "manual_review_pending", createdAt: now }],
        nextCursor: null,
      });
    }
    if (path === `/api/v1/submissions/${submissionId}/reviews`) {
      const result = body && typeof body === "object" && "result" in body ? body.result : "approved";
      return response({ id: reviewId, result, comment: "done", createdAt: now }, 201);
    }
    if (path === `/api/v1/submissions/${submissionId}/run`) {
      return response({ id: reviewId, submissionId, status: "succeeded", attempt: 1, sanitizedResult: { passed: true } });
    }
    if (path === "/api/v1/exams") {
      return response({ items: [{ id: examId, stableCode: "EXAM-001", title: "Exam", scheduledAt: now }], nextCursor: null });
    }
    if (path === `/api/v1/exams/${examId}/attempts`) {
      return response({ id: attemptId, examId, status: "reserved", attemptNumber: 1 }, 201);
    }
    if (path === `/api/v1/exam-attempts/${attemptId}/start`) {
      return response({
        attempt: { id: attemptId, examId, status: "in_progress", attemptNumber: 1 },
        variantSnapshot: {},
        startsAt: now,
        deadlineAt: now,
        submittedAt: null,
        result: null,
      });
    }
    if (path === `/api/v1/exam-attempts/${attemptId}/submit`) {
      return response({
        attempt: { id: attemptId, examId, status: "oral_pending", attemptNumber: 1 },
        variantSnapshot: {},
        startsAt: now,
        deadlineAt: now,
        submittedAt: now,
        result: { score: 75 },
      });
    }
    if (path === "/api/v1/admin/users") {
      return response({ items: [userForEmail("admin@example.local")], nextCursor: null });
    }
    if (path === "/api/v1/admin/feature-flags") {
      return response({ items: [{ key: "runner.enabled", enabled: options.runnerEnabled ?? false, version: 1 }] });
    }
    if (path === "/api/v1/admin/analytics/learning") {
      return response({ learners: 1, submissions: 1, approvedSubmissions: 0, examAttempts: 0, passedExamAttempts: 0 });
    }
    if (path === "/api/v1/admin/curriculum/versions") {
      return response({ items: [{ id: reviewId, version: "v4.0", status: "published", contentHash: "hash" }], nextCursor: null });
    }
    return response({ error: path }, 404);
  });
  vi.stubGlobal("fetch", fetchMock);
  vi.stubGlobal("crypto", { randomUUID: vi.fn(() => "idempotency-key") });
  return { calls, fetchMock };
}

function stubMatchMedia(matches = false) {
  const matchMedia = (query: string) => ({
    matches,
    media: query,
    onchange: null,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
  });
  vi.stubGlobal("matchMedia", matchMedia);
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: matchMedia,
  });
}

function renderApp(initialEntries = ["/"]) {
  if (typeof window.matchMedia !== "function") {
    stubMatchMedia(false);
  }
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    stubMatchMedia(false);
    localStorage.clear();
  });

  it("renders the local MVP shell for a learner with disabled gated features", async () => {
    installFetch();
    renderApp();

    expect(screen.getByRole("heading", { name: "ダッシュボード" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "ローカルログイン" })).toBeInTheDocument();
    expect(screen.getAllByText("TAIGA NOVA").length).toBeGreaterThan(0);
    expect(await screen.findByRole("heading", { name: "基本情報試験まで" })).toBeInTheDocument();
    expect(screen.getAllByText("69日").length).toBeGreaterThan(0);
    expect(await screen.findByText("正常")).toBeInTheDocument();
    expect(await screen.findByText("上山 虎雅 · 学習者")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "実行環境" }));
    expect(screen.getByRole("button", { name: "提出を実行確認する" })).toBeDisabled();
    expect(screen.getByText("実行結果はまだありません。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "試験" }));
    expect(screen.getByRole("button", { name: "試験を開始" })).toBeDisabled();
    expect(screen.getByText("試験結果はまだありません。")).toBeInTheDocument();
  });

  it("creates a demo submission and can run it when the runner is enabled", async () => {
    installFetch({ runnerEnabled: true });
    renderApp();

    await screen.findByText("上山 虎雅 · 学習者");
    fireEvent.click(screen.getByRole("link", { name: "課題" }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "デモ回答を提出" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "デモ回答を提出" }));

    expect(await screen.findByText(`提出を作成しました: ${submissionId}`)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "実行環境" }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "提出を実行確認する" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "提出を実行確認する" }));
    expect(await screen.findByText("完了")).toBeInTheDocument();
  });

  it("hides local-only demo submission controls in production", async () => {
    installFetch({ appEnv: "production" });
    renderApp(["/assignments"]);

    expect(await screen.findByText("Typing basics")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "デモ回答を提出" })).not.toBeInTheDocument();
    expect(screen.queryByText("新しい提出はまだありません。")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "ログアウト" })).toBeInTheDocument();
  });

  it("shows the production password login before the app shell", async () => {
    installFetch({ appEnv: "production", requireLogin: true });
    renderApp(["/dashboard"]);

    expect(await screen.findByRole("heading", { name: "ログイン" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "ダッシュボード" })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("メールアドレス"), {
      target: { value: "admin@example.local" },
    });
    fireEvent.change(screen.getByLabelText("パスワード"), {
      target: { value: "password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "ログイン" }));

    expect(await screen.findByRole("heading", { name: "ダッシュボード" })).toBeInTheDocument();
  });

  it("renders populated dashboard rows, opens assignment detail, and handles mobile drawer", async () => {
    stubMatchMedia(true);
    installFetch({ todayAssignment: true });
    renderApp();

    expect(await screen.findByText("Typing basics")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "ナビゲーションを開く" }));
    expect(screen.getAllByRole("button", { name: "ナビゲーションを閉じる" })[0]).toHaveAttribute(
      "aria-expanded",
      "true",
    );
    expect(screen.getByRole("link", { name: "ダッシュボード" })).toHaveFocus();
    fireEvent.keyDown(window, { key: "Tab", shiftKey: true });
    expect(screen.getByLabelText("ローカル利用者")).toHaveFocus();
    fireEvent.keyDown(window, { key: "Tab" });
    expect(screen.getByRole("link", { name: "ダッシュボード" })).toHaveFocus();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.getByRole("button", { name: "ナビゲーションを開く" })).toHaveAttribute(
      "aria-expanded",
      "false",
    );

    fireEvent.click(screen.getByRole("button", { name: "ナビゲーションを開く" }));
    fireEvent.click(screen.getByRole("link", { name: "課題" }));
    fireEvent.click(await screen.findByRole("button", { name: "詳細を開く" }));
    expect(screen.getByLabelText("課題詳細")).toHaveTextContent("Typing basics");
  });

  it("shows the schedule calendar and opens linked assignments", async () => {
    installFetch();
    renderApp(["/schedule"]);

    expect(await screen.findByRole("heading", { name: "スケジュール" })).toBeInTheDocument();
    expect(await screen.findAllByText("基本情報：現在地確認")).not.toHaveLength(0);
    expect(await screen.findAllByText("遅延")).not.toHaveLength(0);
    fireEvent.click(await screen.findByRole("button", { name: "課題詳細へ" }));
    expect(await screen.findByRole("heading", { name: "課題" })).toBeInTheDocument();
  });

  it("renders deadline and operating metrics without the old progress image", async () => {
    installFetch({ completedWeeks: null });
    renderApp();

    expect(await screen.findByRole("heading", { name: "基本情報試験まで" })).toBeInTheDocument();
    expect(screen.queryByRole("progressbar", { name: "学習進捗" })).not.toBeInTheDocument();
    expect(screen.getByLabelText("運用指標")).toHaveTextContent("Piscineまで");
    expect(screen.getByLabelText("運用指標")).toHaveTextContent("遅延");
  });

  it("renders the TAIGA NOVA off-orbit not found route", async () => {
    installFetch();
    renderApp(["/missing"]);

    expect(screen.getByRole("heading", { name: "ページが見つかりません" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "ダッシュボードへ戻る" })).toBeInTheDocument();
  });

  it("loads admin-only panels and reviews pending submissions", async () => {
    const { calls } = installFetch();
    renderApp();

    fireEvent.change(await screen.findByLabelText("ローカル利用者"), {
      target: { value: "admin@example.local" },
    });

    expect(await screen.findByText("上山 捷馬 · 管理者")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "管理" }));
    expect(await screen.findByText("公開済み")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("link", { name: "レビュー" }));
    fireEvent.click(screen.getByRole("button", { name: `${submissionId.slice(0, 8)}に修正依頼` }));

    expect(await screen.findByText("修正依頼")).toBeInTheDocument();
    expect(calls.find((call) => call.path.endsWith("/reviews"))?.body).toMatchObject({
      result: "needs_revision",
    });
  });

  it("runs the server-authoritative exam flow only when enabled", async () => {
    installFetch({ examEnabled: true });
    renderApp();

    fireEvent.click(await screen.findByRole("link", { name: "試験" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "試験を開始" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "試験を開始" }));

    expect(await screen.findByText("口頭確認待ち")).toBeInTheDocument();
  });
});
