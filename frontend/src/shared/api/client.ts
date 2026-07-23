import { z } from "zod";

const healthSchema = z.object({
  status: z.string(),
  app_env: z.string(),
  runner_enabled: z.boolean(),
  exam_enabled: z.boolean(),
});

export type Health = z.infer<typeof healthSchema>;

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<Health> {
  const response = await fetch(`${apiBaseUrl}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.status}`);
  }
  return healthSchema.parse(await response.json());
}
