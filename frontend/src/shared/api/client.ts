import { z } from "zod";

const healthSchema = z.object({
  status: z.string(),
  app_env: z.string().optional(),
  runner_enabled: z.boolean().optional(),
  exam_enabled: z.boolean().optional(),
});

export type Health = z.infer<typeof healthSchema>;

const configuredApiBaseUrl = import.meta.env.VITE_API_BASE_URL;
const apiBaseUrl = resolveApiBaseUrl(configuredApiBaseUrl);
const authStorageKey = "taiga.localUser";
const requestTimeoutMs = 20_000;
const useLocalAuth = !import.meta.env.PROD;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function resolveApiBaseUrl(value: string | undefined): string {
  if (import.meta.env.PROD && !value) {
    throw new Error("VITE_API_BASE_URL is required for production builds.");
  }
  const resolved = value ?? "http://localhost:8000";
  if (import.meta.env.PROD && !resolved.startsWith("https://")) {
    throw new Error("VITE_API_BASE_URL must use HTTPS in production.");
  }
  return resolved.replace(/\/$/, "");
}

const assignmentSummarySchema = z.object({
  id: z.string(),
  stableCode: z.string(),
  title: z.string(),
  scheduledDate: z.string(),
  status: z.string(),
});

const userProfileSchema = z.object({
  id: z.string(),
  displayName: z.string(),
  role: z.enum(["learner", "reviewer", "admin"]),
  status: z.string(),
  timezone: z.string(),
});

const dashboardSchema = z.object({
  today: z.array(assignmentSummarySchema),
  overdue: z.array(assignmentSummarySchema),
  nextExam: z
    .object({
      id: z.string(),
      stableCode: z.string(),
      scheduledAt: z.string(),
      status: z.string(),
    })
    .nullable(),
  rank: z.string().nullable(),
  capabilityGaps: z.array(z.string()),
});

const assignmentPageSchema = z.object({
  items: z.array(assignmentSummarySchema),
  nextCursor: z.string().nullable(),
});

const assignmentDetailSchema = z.object({
  assignment: assignmentSummarySchema,
  instructions: z.array(z.string()),
  submissionSpec: z.record(z.string(), z.unknown()),
  submissions: z.array(z.unknown()),
});

const scheduleItemSchema = z.object({
  id: z.string(),
  scheduleKey: z.string(),
  date: z.string(),
  startAt: z.string().nullable(),
  endAt: z.string().nullable(),
  title: z.string(),
  description: z.string(),
  itemType: z.string(),
  assignmentId: z.string().nullable(),
  milestoneKey: z.string().nullable(),
  priority: z.number(),
  dueAt: z.string().nullable(),
  sourceUrl: z.string().nullable(),
  isRequired: z.boolean(),
  displayStatus: z.string(),
  isOverdue: z.boolean(),
  overdueDays: z.number(),
  isToday: z.boolean(),
  assignmentUrl: z.string().nullable(),
  metadata: z.record(z.string(), z.unknown()),
});

const scheduleDaySchema = z.object({
  date: z.string(),
  representativeStatus: z.string(),
  isToday: z.boolean(),
  items: z.array(scheduleItemSchema),
});

const schedulePageSchema = z.object({
  fromDate: z.string(),
  toDate: z.string(),
  days: z.array(scheduleDaySchema),
});

const scheduleSummarySchema = z.object({
  todayCount: z.number(),
  learnerOverdueCount: z.number(),
  reviewWaitingCount: z.number(),
  nextImportantDate: z.string().nullable(),
  nextImportantTitle: z.string().nullable(),
  daysUntilPiscine: z.number(),
});

const progressSchema = z.object({
  completedWeeks: z.number().nullable().optional(),
  capabilities: z.array(z.object({ code: z.string(), level: z.number() })),
  rank: z.string().nullable(),
});

const uploadSessionSchema = z.object({
  id: z.string(),
  status: z.string(),
  uploadUrl: z.string().nullable().optional(),
  expiresAt: z.string(),
  rejectionCode: z.string().nullable().optional(),
});

const submissionSchema = z.object({
  id: z.string(),
  assignmentId: z.string(),
  version: z.number(),
  status: z.string(),
  createdAt: z.string(),
});

const reviewQueueSchema = z.object({
  items: z.array(submissionSchema),
  nextCursor: z.string().nullable(),
});

const reviewSchema = z.object({
  id: z.string(),
  result: z.string(),
  comment: z.string(),
  createdAt: z.string(),
});

const runnerJobSchema = z.object({
  id: z.string(),
  submissionId: z.string(),
  status: z.string(),
  attempt: z.number(),
  sanitizedResult: z.record(z.string(), z.unknown()).nullable(),
});

const examPageSchema = z.object({
  items: z.array(
    z.object({
      id: z.string(),
      stableCode: z.string(),
      title: z.string(),
      scheduledAt: z.string(),
    }),
  ),
  nextCursor: z.string().nullable(),
});

const examAttemptSchema = z.object({
  id: z.string(),
  examId: z.string(),
  status: z.string(),
  attemptNumber: z.number(),
});

const examAttemptDetailSchema = z.object({
  attempt: examAttemptSchema,
  variantSnapshot: z.record(z.string(), z.unknown()),
  startsAt: z.string().nullable(),
  deadlineAt: z.string().nullable(),
  submittedAt: z.string().nullable(),
  result: z.record(z.string(), z.unknown()).nullable(),
});

const userPageSchema = z.object({
  items: z.array(userProfileSchema),
  nextCursor: z.string().nullable(),
});

const featureFlagListSchema = z.object({
  items: z.array(z.object({ key: z.string(), enabled: z.boolean(), version: z.number() })),
});

const analyticsSchema = z.object({
  learners: z.number(),
  submissions: z.number(),
  approvedSubmissions: z.number(),
  examAttempts: z.number(),
  passedExamAttempts: z.number(),
});

const curriculumVersionPageSchema = z.object({
  items: z.array(
    z.object({
      id: z.string(),
      version: z.string(),
      status: z.string(),
      contentHash: z.string(),
    }),
  ),
  nextCursor: z.string().nullable(),
});

export type UserProfile = z.infer<typeof userProfileSchema>;
export type AssignmentSummary = z.infer<typeof assignmentSummarySchema>;
export type Dashboard = z.infer<typeof dashboardSchema>;
export type AssignmentPage = z.infer<typeof assignmentPageSchema>;
export type AssignmentDetail = z.infer<typeof assignmentDetailSchema>;
export type ScheduleItem = z.infer<typeof scheduleItemSchema>;
export type ScheduleDay = z.infer<typeof scheduleDaySchema>;
export type SchedulePage = z.infer<typeof schedulePageSchema>;
export type ScheduleSummary = z.infer<typeof scheduleSummarySchema>;
export type ScheduleItemInput = {
  date?: string;
  title?: string;
  description?: string;
  itemType?: string;
  assignmentId?: string | null;
  milestoneKey?: string | null;
  statusOverride?: string | null;
  priority?: number;
  dueAt?: string | null;
  sourceUrl?: string | null;
  isRequired?: boolean;
  metadata?: Record<string, unknown>;
};
export type Progress = z.infer<typeof progressSchema>;
export type UploadSession = z.infer<typeof uploadSessionSchema>;
export type Submission = z.infer<typeof submissionSchema>;
export type ReviewQueue = z.infer<typeof reviewQueueSchema>;
export type Review = z.infer<typeof reviewSchema>;
export type RunnerJob = z.infer<typeof runnerJobSchema>;
export type ExamPage = z.infer<typeof examPageSchema>;
export type ExamAttempt = z.infer<typeof examAttemptSchema>;
export type ExamAttemptDetail = z.infer<typeof examAttemptDetailSchema>;
export type UserPage = z.infer<typeof userPageSchema>;
export type FeatureFlagList = z.infer<typeof featureFlagListSchema>;
export type Analytics = z.infer<typeof analyticsSchema>;
export type CurriculumVersionPage = z.infer<typeof curriculumVersionPageSchema>;

export function getStoredLocalUser(): string {
  return window.localStorage.getItem(authStorageKey) ?? "taiga@example.local";
}

export function setStoredLocalUser(email: string): void {
  window.localStorage.setItem(authStorageKey, email);
}

function authHeaders(): HeadersInit {
  return useLocalAuth ? { Authorization: `Bearer local:${getStoredLocalUser()}` } : {};
}

async function fetchWithTimeout(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), requestTimeoutMs);
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("API request timed out", 0);
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function apiGet<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const response = await fetchWithTimeout(`${apiBaseUrl}/api/v1${path}`, {
    credentials: "include",
    headers: authHeaders(),
  });
  if (!response.ok) {
    throw new ApiError(`API request failed: ${response.status}`, response.status);
  }
  return schema.parse(await response.json());
}

async function apiPost<T>(path: string, body: unknown, schema: z.ZodType<T>): Promise<T> {
  const response = await fetchWithTimeout(`${apiBaseUrl}/api/v1${path}`, {
    method: "POST",
    credentials: "include",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiError(`API request failed: ${response.status}`, response.status);
  }
  return schema.parse(await response.json());
}

async function apiPatch<T>(path: string, body: unknown, schema: z.ZodType<T>): Promise<T> {
  const response = await fetchWithTimeout(`${apiBaseUrl}/api/v1${path}`, {
    method: "PATCH",
    credentials: "include",
    headers: {
      ...authHeaders(),
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new ApiError(`API request failed: ${response.status}`, response.status);
  }
  return schema.parse(await response.json());
}

async function apiDelete(path: string): Promise<void> {
  const response = await fetchWithTimeout(`${apiBaseUrl}/api/v1${path}`, {
    method: "DELETE",
    credentials: "include",
    headers: {
      ...authHeaders(),
      "Idempotency-Key": crypto.randomUUID(),
    },
  });
  if (!response.ok) {
    throw new ApiError(`API request failed: ${response.status}`, response.status);
  }
}

export async function getHealth(): Promise<Health> {
  const response = await fetchWithTimeout(`${apiBaseUrl}/api/health`);
  if (!response.ok) {
    throw new ApiError(`Health check failed: ${response.status}`, response.status);
  }
  return healthSchema.parse(await response.json());
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) {
      return "サーバーを起動しています。初回のみ数十秒かかる場合があります。";
    }
    if (error.status === 401) {
      return "認証セッションを確認できません。Cloudflare Accessで再認証してください。";
    }
    if (error.status === 403) {
      return "このメールアドレスにはTAIGA NOVAへのアクセス権がありません。";
    }
    if (error.status >= 500) {
      return "サーバーで問題が発生しました。時間をおいて再試行してください。";
    }
  }
  return "通信に失敗しました。時間をおいて再試行してください。";
}

export function getMe(): Promise<UserProfile> {
  return apiGet("/me", userProfileSchema);
}

export function getDashboard(): Promise<Dashboard> {
  return apiGet("/dashboard", dashboardSchema);
}

export function getAssignments(): Promise<AssignmentPage> {
  return apiGet("/assignments", assignmentPageSchema);
}

export function getAssignment(id: string): Promise<AssignmentDetail> {
  return apiGet(`/assignments/${id}`, assignmentDetailSchema);
}

export function getSchedule(fromDate: string, toDate: string): Promise<SchedulePage> {
  return apiGet(`/schedule?from=${fromDate}&to=${toDate}`, schedulePageSchema);
}

export function getScheduleDay(date: string): Promise<ScheduleDay> {
  return apiGet(`/schedule/${date}`, scheduleDaySchema);
}

export function getScheduleSummary(): Promise<ScheduleSummary> {
  return apiGet("/schedule/summary", scheduleSummarySchema);
}

export function createScheduleItem(input: ScheduleItemInput): Promise<ScheduleItem> {
  return apiPost("/admin/schedule-items", input, scheduleItemSchema);
}

export function updateScheduleItem(id: string, input: ScheduleItemInput): Promise<ScheduleItem> {
  return apiPatch(`/admin/schedule-items/${id}`, input, scheduleItemSchema);
}

export function deleteScheduleItem(id: string): Promise<void> {
  return apiDelete(`/admin/schedule-items/${id}`);
}

export function getProgress(): Promise<Progress> {
  return apiGet("/progress", progressSchema);
}

export function getReviewQueue(): Promise<ReviewQueue> {
  return apiGet("/reviews/queue", reviewQueueSchema);
}

export async function createDemoSubmission(assignmentId: string): Promise<Submission> {
  const sha256 = "a".repeat(64);
  const upload = await apiPost(
    "/uploads/presign",
    { originalName: "answer.md", mediaType: "text/markdown", sizeBytes: 10, sha256 },
    uploadSessionSchema,
  );
  await apiPost(`/uploads/${upload.id}/complete`, { sizeBytes: 10, sha256 }, uploadSessionSchema);
  return apiPost(
    `/assignments/${assignmentId}/submissions`,
    { sourceType: "file_upload", repositoryUrl: null, commitHash: null, uploadIds: [upload.id] },
    submissionSchema,
  );
}

export function runSubmission(submissionId: string): Promise<RunnerJob> {
  return apiPost(`/submissions/${submissionId}/run`, { reason: "manual" }, runnerJobSchema);
}

export function getExams(): Promise<ExamPage> {
  return apiGet("/exams", examPageSchema);
}

export function reviewSubmission(
  submissionId: string,
  result: "approved" | "needs_revision",
): Promise<Review> {
  return apiPost(
    `/submissions/${submissionId}/reviews`,
    {
      result,
      rubric: { correctness: "checked", clarity: "checked" },
      comment:
        result === "approved"
          ? "Approved from local MVP review."
          : "Please revise the answer and resubmit.",
    },
    reviewSchema,
  );
}

export function createExamAttempt(examId: string): Promise<ExamAttempt> {
  return apiPost(`/exams/${examId}/attempts`, {}, examAttemptSchema);
}

export function startExamAttempt(attemptId: string): Promise<ExamAttemptDetail> {
  return apiPost(`/exam-attempts/${attemptId}/start`, { acknowledgeRules: true }, examAttemptDetailSchema);
}

export function submitExamAttempt(attemptId: string): Promise<ExamAttemptDetail> {
  return apiPost(
    `/exam-attempts/${attemptId}/submit`,
    { answers: { q1: "local MVP answer" }, submissionId: null },
    examAttemptDetailSchema,
  );
}

export function getAdminUsers(): Promise<UserPage> {
  return apiGet("/admin/users", userPageSchema);
}

export function getFeatureFlags(): Promise<FeatureFlagList> {
  return apiGet("/admin/feature-flags", featureFlagListSchema);
}

export function getAnalytics(): Promise<Analytics> {
  return apiGet("/admin/analytics/learning", analyticsSchema);
}

export function getCurriculumVersions(): Promise<CurriculumVersionPage> {
  return apiGet("/admin/curriculum/versions", curriculumVersionPageSchema);
}
