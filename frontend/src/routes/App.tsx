import { useQuery } from "@tanstack/react-query";

import { getHealth } from "../shared/api/client";

export function App() {
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });

  return (
    <main className="shell">
      <section className="workspace">
        <div>
          <p className="eyebrow">Local MVP</p>
          <h1>Project Taiga</h1>
          <p className="summary">
            Local learning workflow foundation with backend, frontend, worker, runner controller,
            and PostgreSQL services.
          </p>
        </div>
        <dl className="status-grid" aria-label="Service status">
          <div>
            <dt>API</dt>
            <dd>{health.isSuccess ? health.data.status : "checking"}</dd>
          </div>
          <div>
            <dt>Runner</dt>
            <dd>{health.data?.runner_enabled ? "enabled" : "disabled"}</dd>
          </div>
          <div>
            <dt>Exam</dt>
            <dd>{health.data?.exam_enabled ? "enabled" : "disabled"}</dd>
          </div>
        </dl>
      </section>
    </main>
  );
}
