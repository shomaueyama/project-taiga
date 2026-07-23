import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the local MVP shell", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL) => {
        const url = String(input);
        if (url.endsWith("/health")) {
          return {
            ok: true,
            json: async () => ({
              status: "ok",
              app_env: "local",
              runner_enabled: false,
              exam_enabled: false,
            }),
          };
        }
        if (url.endsWith("/me")) {
          return {
            ok: true,
            json: async () => ({
              id: "00000000-0000-0000-0000-000000000001",
              displayName: "Taiga Learner",
              role: "learner",
              status: "active",
              timezone: "Asia/Tokyo",
            }),
          };
        }
        if (url.endsWith("/dashboard")) {
          return {
            ok: true,
            json: async () => ({
              today: [],
              overdue: [],
              nextExam: null,
              rank: null,
              capabilityGaps: [],
            }),
          };
        }
        if (url.endsWith("/assignments")) {
          return { ok: true, json: async () => ({ items: [], nextCursor: null }) };
        }
        if (url.endsWith("/reviews/queue")) {
          return { ok: true, json: async () => ({ items: [], nextCursor: null }) };
        }
        return {
          ok: true,
          json: async () => ({ completedWeeks: 0, capabilities: [], rank: null }),
        };
      }),
    );

    render(
      <QueryClientProvider client={new QueryClient()}>
        <App />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "Project Taiga" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Local Login" })).toBeInTheDocument();
    expect(await screen.findByText("ok")).toBeInTheDocument();
  });
});
