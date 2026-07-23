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

export type UserProfile = z.infer<typeof userProfileSchema>;
export type AssignmentSummary = z.infer<typeof assignmentSummarySchema>;
export type Dashboard = z.infer<typeof dashboardSchema>;
export type AssignmentPage = z.infer<typeof assignmentPageSchema>;
export type AssignmentDetail = z.infer<typeof assignmentDetailSchema>;
export type Progress = z.infer<typeof progressSchema>;

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
