import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import {
  getAssignments,
  getDashboard,
  getExams,
  getHealth,
  getMe,
  getProgress,
  getReviewQueue,
  getStoredLocalUser,
  setStoredLocalUser,
} from "../shared/api/client";

export function App() {
  const [localUser, setLocalUser] = useState(getStoredLocalUser());
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const me = useQuery({ queryKey: ["me", localUser], queryFn: getMe });
  const dashboard = useQuery({ queryKey: ["dashboard", localUser], queryFn: getDashboard });
  const assignments = useQuery({ queryKey: ["assignments", localUser], queryFn: getAssignments });
  const progress = useQuery({ queryKey: ["progress", localUser], queryFn: getProgress });
  const reviewQueue = useQuery({
    queryKey: ["review-queue", localUser],
    queryFn: getReviewQueue,
    retry: false,
  });
  const exams = useQuery({ queryKey: ["exams", localUser], queryFn: getExams });

  function handleLocalUserChange(email: string) {
    setStoredLocalUser(email);
    setLocalUser(email);
  }

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
      <section className="app-grid">
        <aside className="panel login-panel">
          <h2>Local Login</h2>
          <select
            aria-label="Local user"
            value={localUser}
            onChange={(event) => handleLocalUserChange(event.target.value)}
          >
            <option value="taiga@example.local">taiga@example.local</option>
            <option value="reviewer@example.local">reviewer@example.local</option>
            <option value="admin@example.local">admin@example.local</option>
          </select>
          <p>{me.data ? `${me.data.displayName} · ${me.data.role}` : "Not signed in"}</p>
        </aside>
        <section className="panel">
          <h2>Dashboard</h2>
          <div className="metric-row">
            <span>Today</span>
            <strong>{dashboard.data?.today.length ?? 0}</strong>
          </div>
          <div className="metric-row">
            <span>Completed weeks</span>
            <strong>{progress.data?.completedWeeks ?? 0}</strong>
          </div>
          <div className="metric-row">
            <span>Next exam</span>
            <strong>{dashboard.data?.nextExam?.stableCode ?? "none"}</strong>
          </div>
        </section>
        <section className="panel assignments-panel">
          <h2>Assignments</h2>
          <div className="assignment-list">
            {(assignments.data?.items ?? []).slice(0, 8).map((assignment) => (
              <article className="assignment-row" key={assignment.id}>
                <div>
                  <strong>{assignment.title}</strong>
                  <span>{assignment.stableCode}</span>
                </div>
                <time>{assignment.scheduledDate}</time>
              </article>
            ))}
          </div>
        </section>
        <section className="panel">
          <h2>Review</h2>
          <div className="metric-row">
            <span>Pending</span>
            <strong>{reviewQueue.data?.items.length ?? 0}</strong>
          </div>
        </section>
        <section className="panel">
          <h2>Exam</h2>
          <div className="metric-row">
            <span>Scheduled</span>
            <strong>{exams.data?.items.length ?? 0}</strong>
          </div>
        </section>
      </section>
    </main>
  );
}
