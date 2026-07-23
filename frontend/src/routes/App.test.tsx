import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the local MVP shell", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          status: "ok",
          app_env: "local",
          runner_enabled: false,
          exam_enabled: false,
        }),
      })),
    );

    render(
      <QueryClientProvider client={new QueryClient()}>
        <App />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("heading", { name: "Project Taiga" })).toBeInTheDocument();
    expect(await screen.findByText("ok")).toBeInTheDocument();
  });
});
