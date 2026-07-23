import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  createDemoSubmission,
  createExamAttempt,
  getAssignments,
  getAdminUsers,
  getAnalytics,
  getAssignment,
  getCurriculumVersions,
  getDashboard,
  getExams,
  getFeatureFlags,
  getHealth,
  getMe,
  getProgress,
  getReviewQueue,
  getStoredLocalUser,
  reviewSubmission,
  runSubmission,
  setStoredLocalUser,
  startExamAttempt,
  submitExamAttempt,
} from "../shared/api/client";

export function App() {
  const queryClient = useQueryClient();
  const [localUser, setLocalUser] = useState(getStoredLocalUser());
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(null);
  const [lastSubmissionId, setLastSubmissionId] = useState<string | null>(null);
  const [lastRunnerStatus, setLastRunnerStatus] = useState<string | null>(null);
  const [lastReviewResult, setLastReviewResult] = useState<string | null>(null);
  const [lastExamStatus, setLastExamStatus] = useState<string | null>(null);
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const me = useQuery({ queryKey: ["me", localUser], queryFn: getMe });
  const isSignedIn = me.isSuccess;
  const canReview = me.data?.role === "reviewer" || me.data?.role === "admin";
  const dashboard = useQuery({
    queryKey: ["dashboard", localUser],
    queryFn: getDashboard,
    enabled: isSignedIn,
  });
  const assignments = useQuery({
    queryKey: ["assignments", localUser],
    queryFn: getAssignments,
    enabled: isSignedIn,
  });
  const selectedAssignment = selectedAssignmentId ?? assignments.data?.items[0]?.id ?? null;
  const assignmentDetail = useQuery({
    queryKey: ["assignment-detail", localUser, selectedAssignment],
    queryFn: () => getAssignment(selectedAssignment ?? ""),
    enabled: isSignedIn && selectedAssignment !== null,
  });
  const progress = useQuery({
    queryKey: ["progress", localUser],
    queryFn: getProgress,
    enabled: isSignedIn,
  });
  const reviewQueue = useQuery({
    queryKey: ["review-queue", localUser],
    queryFn: getReviewQueue,
    enabled: canReview,
    retry: false,
  });
  const exams = useQuery({ queryKey: ["exams", localUser], queryFn: getExams, enabled: isSignedIn });
  const adminUsers = useQuery({
    queryKey: ["admin-users", localUser],
    queryFn: getAdminUsers,
    enabled: me.data?.role === "admin",
  });
  const featureFlags = useQuery({
    queryKey: ["feature-flags", localUser],
    queryFn: getFeatureFlags,
    enabled: me.data?.role === "admin",
  });
  const analytics = useQuery({
    queryKey: ["analytics", localUser],
    queryFn: getAnalytics,
    enabled: me.data?.role === "admin",
  });
  const curriculumVersions = useQuery({
    queryKey: ["curriculum-versions", localUser],
    queryFn: getCurriculumVersions,
    enabled: me.data?.role === "admin",
  });

  const submitAssignment = useMutation({
    mutationFn: (assignmentId: string) => createDemoSubmission(assignmentId),
    onSuccess: async (submission) => {
      setLastSubmissionId(submission.id);
      await queryClient.invalidateQueries({ queryKey: ["assignments", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["assignment-detail", localUser] });
    },
  });
  const runLastSubmission = useMutation({
    mutationFn: (submissionId: string) => runSubmission(submissionId),
    onSuccess: (job) => setLastRunnerStatus(job.status),
  });
  const reviewPendingSubmission = useMutation({
    mutationFn: (result: "approved" | "needs_revision") => {
      const submissionId = reviewQueue.data?.items[0]?.id;
      if (!submissionId) {
        throw new Error("No pending submission");
      }
      return reviewSubmission(submissionId, result);
    },
    onSuccess: async (review) => {
      setLastReviewResult(review.result);
      await queryClient.invalidateQueries({ queryKey: ["review-queue", localUser] });
    },
  });
  const runExamFlow = useMutation({
    mutationFn: async (examId: string) => {
      const attempt = await createExamAttempt(examId);
      const started = await startExamAttempt(attempt.id);
      if (started.attempt.status !== "in_progress") {
        return started;
      }
      return submitExamAttempt(started.attempt.id);
    },
    onSuccess: (attempt) => setLastExamStatus(attempt.attempt.status),
  });

  function handleLocalUserChange(email: string) {
    setStoredLocalUser(email);
    setLocalUser(email);
    setSelectedAssignmentId(null);
    setLastSubmissionId(null);
    setLastRunnerStatus(null);
    setLastReviewResult(null);
    setLastExamStatus(null);
  }

  const firstAssignment = assignments.data?.items[0];
  const pendingReview = reviewQueue.data?.items[0];
  const firstExam = exams.data?.items[0];
  const runnerDisabled = health.data?.runner_enabled === false;
  const examDisabled = health.data?.exam_enabled === false;

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
          <div className="metric-row">
            <span>Rank</span>
            <strong>{progress.data?.rank ?? "not ranked"}</strong>
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
                <div className="row-actions">
                  <time>{assignment.scheduledDate}</time>
                  <button type="button" onClick={() => setSelectedAssignmentId(assignment.id)}>
                    Details
                  </button>
                </div>
              </article>
            ))}
          </div>
          <div className="detail-box" aria-label="Assignment detail">
            <strong>{assignmentDetail.data?.assignment.title ?? "No assignment selected"}</strong>
            <span>{assignmentDetail.data?.assignment.status ?? "empty"}</span>
            <span>Submissions: {assignmentDetail.data?.submissions.length ?? 0}</span>
          </div>
          <button
            type="button"
            disabled={!firstAssignment || submitAssignment.isPending}
            onClick={() => firstAssignment && submitAssignment.mutate(firstAssignment.id)}
          >
            Submit demo answer
          </button>
          <p aria-live="polite">
            {lastSubmissionId
              ? `Submission created: ${lastSubmissionId}`
              : submitAssignment.error
                ? "Submission failed"
                : "No new submission"}
          </p>
        </section>
        <section className="panel">
          <h2>Review</h2>
          <div className="metric-row">
            <span>Pending</span>
            <strong>{reviewQueue.data?.items.length ?? 0}</strong>
          </div>
          <div className="metric-row">
            <span>Selected</span>
            <strong>{pendingReview?.status ?? "none"}</strong>
          </div>
          <div className="button-row">
            <button
              type="button"
              disabled={me.data?.role === "learner" || !pendingReview}
              onClick={() => reviewPendingSubmission.mutate("approved")}
            >
              Approve
            </button>
            <button
              type="button"
              disabled={me.data?.role === "learner" || !pendingReview}
              onClick={() => reviewPendingSubmission.mutate("needs_revision")}
            >
              Request revision
            </button>
          </div>
          <p aria-live="polite">{lastReviewResult ?? "No review action"}</p>
        </section>
        <section className="panel">
          <h2>Runner</h2>
          <div className="metric-row">
            <span>State</span>
            <strong>{runnerDisabled ? "disabled" : "enabled"}</strong>
          </div>
          <button
            type="button"
            disabled={runnerDisabled || !lastSubmissionId}
            onClick={() => lastSubmissionId && runLastSubmission.mutate(lastSubmissionId)}
          >
            Run submission
          </button>
          <p aria-live="polite">{lastRunnerStatus ?? "Runner disabled locally"}</p>
        </section>
        <section className="panel">
          <h2>Exam</h2>
          <div className="metric-row">
            <span>Scheduled</span>
            <strong>{exams.data?.items.length ?? 0}</strong>
          </div>
          <div className="metric-row">
            <span>State</span>
            <strong>{examDisabled ? "disabled" : "enabled"}</strong>
          </div>
          <button
            type="button"
            disabled={examDisabled || !firstExam}
            onClick={() => firstExam && runExamFlow.mutate(firstExam.id)}
          >
            Start exam
          </button>
          <p aria-live="polite">{lastExamStatus ?? "Exam disabled locally"}</p>
        </section>
        <section className="panel admin-panel">
          <h2>Admin</h2>
          <div className="metric-row">
            <span>Users</span>
            <strong>{adminUsers.data?.items.length ?? "restricted"}</strong>
          </div>
          <div className="metric-row">
            <span>Learners</span>
            <strong>{analytics.data?.learners ?? "restricted"}</strong>
          </div>
          <div className="metric-row">
            <span>Curriculum</span>
            <strong>{curriculumVersions.data?.items[0]?.status ?? "restricted"}</strong>
          </div>
          <ul className="flag-list" aria-label="Feature flags">
            {(featureFlags.data?.items ?? []).map((flag) => (
              <li key={flag.key}>
                {flag.key}: {flag.enabled ? "enabled" : "disabled"}
              </li>
            ))}
            {me.data?.role !== "admin" ? <li>Admin role required</li> : null}
          </ul>
        </section>
      </section>
    </main>
  );
}
