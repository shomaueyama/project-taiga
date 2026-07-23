import { z } from "zod";

const healthSchema = z.object({
  status: z.string(),
  app_env: z.string(),
  runner_enabled: z.boolean(),
  exam_enabled: z.boolean(),
});

export type Health = z.infer<typeof healthSchema>;

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const authStorageKey = "taiga.localUser";

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

const progressSchema = z.object({
  completedWeeks: z.number(),
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

const runnerJobSchema = z.object({
  id: z.string(),
  submissionId: z.string(),
  status: z.string(),
  attempt: z.number(),
  sanitizedResult: z.record(z.string(), z.unknown()).nullable(),
});

export type UserProfile = z.infer<typeof userProfileSchema>;
export type AssignmentSummary = z.infer<typeof assignmentSummarySchema>;
export type Dashboard = z.infer<typeof dashboardSchema>;
export type AssignmentPage = z.infer<typeof assignmentPageSchema>;
export type AssignmentDetail = z.infer<typeof assignmentDetailSchema>;
export type Progress = z.infer<typeof progressSchema>;
export type UploadSession = z.infer<typeof uploadSessionSchema>;
export type Submission = z.infer<typeof submissionSchema>;
export type ReviewQueue = z.infer<typeof reviewQueueSchema>;
export type RunnerJob = z.infer<typeof runnerJobSchema>;

export function getStoredLocalUser(): string {
  return window.localStorage.getItem(authStorageKey) ?? "taiga@example.local";
}

export function setStoredLocalUser(email: string): void {
  window.localStorage.setItem(authStorageKey, email);
}

async function apiGet<T>(path: string, schema: z.ZodType<T>): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    headers: { Authorization: `Bearer local:${getStoredLocalUser()}` },
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return schema.parse(await response.json());
}

async function apiPost<T>(path: string, body: unknown, schema: z.ZodType<T>): Promise<T> {
  const response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer local:${getStoredLocalUser()}`,
      "Content-Type": "application/json",
      "Idempotency-Key": crypto.randomUUID(),
    },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return schema.parse(await response.json());
}

export async function getHealth(): Promise<Health> {
  const response = await fetch(`${apiBaseUrl}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return healthSchema.parse(await response.json());
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
