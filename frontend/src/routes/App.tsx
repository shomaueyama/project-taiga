import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  CheckSquare,
  Compass,
  GraduationCap,
  LayoutDashboard,
  Menu,
  PlayCircle,
  Settings,
  Sparkles,
  Telescope,
  X,
} from "lucide-react";
import { useEffect, useRef, useState, type ComponentType } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import novaMark from "../assets/brand/nova-mark.svg";
import orbitIllustration from "../assets/illustrations/nova-orbit.svg";
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
import { formatDate, labelForRole, labelForStatus, shortId } from "../shared/labels";
import { calculateMissionProgress, type MissionProgress } from "../shared/mission";
import { Alert, EmptyState, LoadingState, PageHeader, StatusBadge } from "../shared/ui";

type Role = "learner" | "reviewer" | "admin";
type NavItem = {
  path: string;
  label: string;
  roles: Role[];
  icon: ComponentType<{ size?: number; "aria-hidden"?: boolean }>;
};

const NAV_ITEMS: NavItem[] = [
  { path: "/dashboard", label: "ダッシュボード", roles: ["learner", "reviewer", "admin"], icon: LayoutDashboard },
  { path: "/assignments", label: "課題", roles: ["learner", "admin"], icon: BookOpen },
  { path: "/reviews", label: "レビュー", roles: ["reviewer", "admin"], icon: CheckSquare },
  { path: "/runner", label: "実行環境", roles: ["learner", "admin"], icon: PlayCircle },
  { path: "/exams", label: "試験", roles: ["learner", "admin"], icon: GraduationCap },
  { path: "/admin", label: "管理", roles: ["admin"], icon: Settings },
];

function routeGroup(pathname: string) {
  if (pathname === "/") return "/dashboard";
  return `/${pathname.split("/").filter(Boolean)[0] ?? "dashboard"}`;
}

function routeTitle(pathname: string) {
  const group = routeGroup(pathname);
  return NAV_ITEMS.find((item) => item.path === group)?.label ?? "ページが見つかりません";
}

export function App() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const navigate = useNavigate();
  const activeRoute = routeGroup(location.pathname);
  const routeAssignmentId = location.pathname.match(/^\/assignments\/([^/]+)/)?.[1] ?? null;
  const previousPathRef = useRef(location.pathname);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const [isMobileNavOpen, setMobileNavOpen] = useState(false);
  const [localUser, setLocalUser] = useState(getStoredLocalUser());
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(routeAssignmentId);
  const [lastSubmissionId, setLastSubmissionId] = useState<string | null>(null);
  const [lastRunnerStatus, setLastRunnerStatus] = useState<string | null>(null);
  const [lastReviewResult, setLastReviewResult] = useState<string | null>(null);
  const [lastExamStatus, setLastExamStatus] = useState<string | null>(null);

  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const me = useQuery({ queryKey: ["me", localUser], queryFn: getMe });
  const isSignedIn = me.isSuccess;
  const canReview = me.data?.role === "reviewer" || me.data?.role === "admin";
  const canAdmin = me.data?.role === "admin";
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
  const selectedAssignment =
    routeAssignmentId ?? selectedAssignmentId ?? assignments.data?.items[0]?.id ?? null;
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
  const examEnabled = health.data?.exam_enabled === true;
  const exams = useQuery({
    queryKey: ["exams", localUser],
    queryFn: getExams,
    enabled: isSignedIn && examEnabled,
  });
  const adminUsers = useQuery({
    queryKey: ["admin-users", localUser],
    queryFn: getAdminUsers,
    enabled: canAdmin,
  });
  const featureFlags = useQuery({
    queryKey: ["feature-flags", localUser],
    queryFn: getFeatureFlags,
    enabled: canAdmin,
  });
  const analytics = useQuery({
    queryKey: ["analytics", localUser],
    queryFn: getAnalytics,
    enabled: canAdmin,
  });
  const curriculumVersions = useQuery({
    queryKey: ["curriculum-versions", localUser],
    queryFn: getCurriculumVersions,
    enabled: canAdmin,
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
    mutationFn: ({
      submissionId,
      result,
    }: {
      submissionId: string;
      result: "approved" | "needs_revision";
    }) => reviewSubmission(submissionId, result),
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
    navigate("/dashboard");
  }

  function openAssignment(assignmentId: string) {
    setSelectedAssignmentId(assignmentId);
    navigate(`/assignments/${assignmentId}`);
  }

  const firstAssignment = assignments.data?.items[0];
  const firstExam = exams.data?.items[0];
  const runnerDisabled = health.data?.runner_enabled === false;
  const examDisabled = !examEnabled;
  const visibleNav = NAV_ITEMS.filter((item) => item.roles.includes(me.data?.role ?? "learner"));
  const missionProgress = calculateMissionProgress(progress.data?.completedWeeks);

  useEffect(() => {
    document.title = `${routeTitle(location.pathname)} | TAIGA NOVA`;
    setMobileNavOpen(false);
    if (previousPathRef.current !== location.pathname) {
      document.getElementById("main-content")?.focus();
      previousPathRef.current = location.pathname;
    }
  }, [location.pathname]);

  useEffect(() => {
    if (!isMobileNavOpen) {
      return;
    }
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobileNavOpen(false);
        menuButtonRef.current?.focus();
      }
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [isMobileNavOpen]);

  return (
    <div className={`shell ${isMobileNavOpen ? "nav-open" : ""}`}>
      <a className="skip-link" href="#main-content">
        本文へスキップ
      </a>

      <header className="mobile-topbar">
        <BrandLockup compact />
        <button
          ref={menuButtonRef}
          type="button"
          className="icon-button"
          aria-label={isMobileNavOpen ? "ナビゲーションを閉じる" : "ナビゲーションを開く"}
          aria-expanded={isMobileNavOpen}
          aria-controls="site-sidebar"
          onClick={() => setMobileNavOpen((isOpen) => !isOpen)}
        >
          {isMobileNavOpen ? <X aria-hidden size={22} /> : <Menu aria-hidden size={22} />}
        </button>
      </header>

      {isMobileNavOpen ? (
        <button
          className="nav-backdrop"
          type="button"
          aria-label="ナビゲーションを閉じる"
          onClick={() => {
            setMobileNavOpen(false);
            menuButtonRef.current?.focus();
          }}
        />
      ) : null}

      <aside id="site-sidebar" className="sidebar" aria-label="TAIGA NOVA ナビゲーション">
        <BrandLockup />
        <nav className="nav-panel" aria-label="主要ナビゲーション">
          {visibleNav.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                aria-current={activeRoute === item.path ? "page" : undefined}
              >
                <Icon aria-hidden size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <section className="login-panel" aria-labelledby="local-login-title">
          <h2 id="local-login-title">ローカルログイン</h2>
          <label htmlFor="local-user">利用者</label>
          <select
            id="local-user"
            aria-label="ローカル利用者"
            value={localUser}
            onChange={(event) => handleLocalUserChange(event.target.value)}
          >
            <option value="taiga@example.local">taiga@example.local</option>
            <option value="reviewer@example.local">reviewer@example.local</option>
            <option value="admin@example.local">admin@example.local</option>
          </select>
          <p>{me.data ? `${me.data.displayName} · ${labelForRole(me.data.role)}` : "未認証"}</p>
        </section>
      </aside>

      <div className="main-shell">
        <header className="app-header">
          <div>
            <p className="eyebrow">TAIGA NOVA</p>
            <p className="topbar-title">{routeTitle(location.pathname)}</p>
          </div>
          <dl className="status-grid" aria-label="サービス状態">
            <div>
              <dt>API</dt>
              <dd>{health.isSuccess ? labelForStatus(health.data.status) : "確認中"}</dd>
            </div>
            <div>
              <dt>実行環境</dt>
              <dd>{health.data?.runner_enabled ? "有効" : "停止中"}</dd>
            </div>
            <div>
              <dt>試験</dt>
              <dd>{health.data?.exam_enabled ? "有効" : "停止中"}</dd>
            </div>
          </dl>
        </header>

        <main id="main-content" className="main-content" tabIndex={-1}>
          {me.isError ? (
            <Alert tone="danger">利用者を確認できません。ローカル利用者を選び直してください。</Alert>
          ) : null}
          {activeRoute === "/dashboard" ? (
            <section className="page-stack dashboard-grid" aria-labelledby="dashboard-title">
              <PageHeader
                eyebrow="MISSION CONTROL"
                title="ダッシュボード"
                description="学習の現在地、次に進む課題、ローカル環境の状態を確認できます。"
                titleId="dashboard-title"
              />
              {dashboard.isLoading || progress.isLoading ? <LoadingState /> : null}
              <MissionProgressCard
                progress={missionProgress}
                nextAction={firstAssignment?.title ?? "次の課題を確認"}
              />
              <section className="nova-card task-card" aria-labelledby="today-task-title">
                <div className="section-heading">
                  <p className="eyebrow">TODAY</p>
                  <h2 id="today-task-title">今日の課題</h2>
                </div>
                {(dashboard.data?.today ?? []).length > 0 ? (
                  (dashboard.data?.today ?? []).slice(0, 3).map((assignment) => (
                    <article className="compact-row" key={assignment.id}>
                      <div>
                        <strong>{assignment.title}</strong>
                        <span>{assignment.stableCode}</span>
                      </div>
                      <StatusBadge status={assignment.status} />
                    </article>
                  ))
                ) : (
                  <EmptyState
                    title="今日の課題はありません。"
                    action={<Link className="button-link" to="/assignments">一覧を確認</Link>}
                  />
                )}
              </section>
              <div className="card-grid dashboard-metrics">
                <Metric label="完了週" value={progress.data?.completedWeeks ?? 0} />
                <Metric label="次の試験" value={dashboard.data?.nextExam?.stableCode ?? "予定なし"} />
                <Metric label="ランク" value={progress.data?.rank ?? "未判定"} />
              </div>
              <Alert tone="info">TAIGA NOVAは直接URL、ブラウザ更新、戻る操作に対応しています。</Alert>
            </section>
          ) : null}

          {activeRoute === "/assignments" ? (
            <section className="page-stack" aria-labelledby="assignments-title">
              <PageHeader
                eyebrow="MISSION TASKS"
                title="課題"
                description="取り組む課題と提出状況を確認できます。"
                titleId="assignments-title"
              />
              {assignments.isLoading ? <LoadingState label="課題を読み込み中です" /> : null}
              <div className="assignment-list">
                {(assignments.data?.items ?? []).slice(0, 8).map((assignment) => (
                  <article className="assignment-row" key={assignment.id}>
                    <div>
                      <strong>{assignment.title}</strong>
                      <span>{assignment.stableCode}</span>
                    </div>
                    <div className="row-actions">
                      <time dateTime={assignment.scheduledDate}>
                        {formatDate(assignment.scheduledDate)}
                      </time>
                      <StatusBadge status={assignment.status} />
                      <button type="button" onClick={() => openAssignment(assignment.id)}>
                        詳細を開く
                      </button>
                    </div>
                  </article>
                ))}
              </div>
              {assignments.data?.items.length === 0 ? (
                <EmptyState title="表示できる課題はありません。" />
              ) : null}
              <div className="detail-box" aria-label="課題詳細">
                <strong>{assignmentDetail.data?.assignment.title ?? "課題を選択してください"}</strong>
                <span>
                  状態: <StatusBadge status={assignmentDetail.data?.assignment.status} />
                </span>
                <span>提出履歴: {assignmentDetail.data?.submissions.length ?? 0}件</span>
                {assignmentDetail.isError ? (
                  <Alert tone="danger">課題を読み込めません。権限またはURLを確認してください。</Alert>
                ) : null}
              </div>
              <button
                type="button"
                className="primary-action"
                disabled={!firstAssignment || submitAssignment.isPending}
                onClick={() => firstAssignment && submitAssignment.mutate(firstAssignment.id)}
              >
                デモ回答を提出
              </button>
              <p aria-live="polite">
                {lastSubmissionId
                  ? `提出を作成しました: ${lastSubmissionId}`
                  : submitAssignment.error
                    ? "提出に失敗しました。入力と権限を確認してください。"
                    : "新しい提出はまだありません。"}
              </p>
            </section>
          ) : null}

          {activeRoute === "/reviews" ? (
            <section className="page-stack" aria-labelledby="reviews-title">
              <PageHeader
                eyebrow="REVIEW ORBIT"
                title="レビュー"
                description="提出物を確認し、承認または修正依頼を記録します。"
                titleId="reviews-title"
              />
              {!canReview ? <Alert tone="warning">レビューにはレビュアー以上の権限が必要です。</Alert> : null}
              {reviewQueue.isLoading ? <LoadingState label="レビュー待ちを読み込み中です" /> : null}
              <div className="metric-row">
                <span>レビュー待ち</span>
                <strong>{reviewQueue.data?.items.length ?? 0}</strong>
              </div>
              {(reviewQueue.data?.items ?? []).slice(0, 5).map((submission) => (
                <article className="review-row" key={submission.id}>
                  <div>
                    <strong>提出 {shortId(submission.id)}</strong>
                    <StatusBadge status={submission.status} />
                  </div>
                  <div className="button-row">
                    <button
                      type="button"
                      disabled={!canReview || reviewPendingSubmission.isPending}
                      onClick={() =>
                        reviewPendingSubmission.mutate({
                          submissionId: submission.id,
                          result: "approved",
                        })
                      }
                    >
                      {shortId(submission.id)}を承認
                    </button>
                    <button
                      type="button"
                      className="danger-action"
                      disabled={!canReview || reviewPendingSubmission.isPending}
                      onClick={() =>
                        reviewPendingSubmission.mutate({
                          submissionId: submission.id,
                          result: "needs_revision",
                        })
                      }
                    >
                      {shortId(submission.id)}に修正依頼
                    </button>
                  </div>
                </article>
              ))}
              {canReview && reviewQueue.data?.items.length === 0 ? (
                <EmptyState title="レビュー待ちの提出はありません。" />
              ) : null}
              <p aria-live="polite">
                {lastReviewResult ? labelForStatus(lastReviewResult) : "レビュー操作はまだありません。"}
              </p>
            </section>
          ) : null}

          {activeRoute === "/runner" ? (
            <section className="page-stack" aria-labelledby="runner-title">
              <PageHeader
                eyebrow="LOCAL RUNNER"
                title="実行環境"
                description="ローカル環境では安全確認が完了するまでコード実行は停止しています。"
                titleId="runner-title"
              />
              <FeaturePanel
                icon={Compass}
                title="実行環境は停止中です"
                body="これは利用者の操作ミスではなく、ローカルMVPの安全設定です。"
              />
              <div className="metric-row">
                <span>状態</span>
                <strong>{runnerDisabled ? "停止中" : "有効"}</strong>
              </div>
              <button
                type="button"
                disabled={runnerDisabled || !lastSubmissionId || runLastSubmission.isPending}
                onClick={() => lastSubmissionId && runLastSubmission.mutate(lastSubmissionId)}
              >
                提出を実行確認する
              </button>
              <p aria-live="polite">
                {lastRunnerStatus ? labelForStatus(lastRunnerStatus) : "実行結果はまだありません。"}
              </p>
            </section>
          ) : null}

          {activeRoute === "/exams" ? (
            <section className="page-stack" aria-labelledby="exams-title">
              <PageHeader
                eyebrow="EXAM GATE"
                title="試験"
                description="試験はサーバー時刻と状態遷移を基準に扱います。"
                titleId="exams-title"
              />
              {examDisabled ? (
                <FeaturePanel
                  icon={Telescope}
                  title="試験機能は停止中です"
                  body="ローカル環境では開始操作を送信しません。利用可能になった試験だけを表示します。"
                />
              ) : null}
              <div className="metric-row">
                <span>予定数</span>
                <strong>{exams.data?.items.length ?? 0}</strong>
              </div>
              <button
                type="button"
                disabled={examDisabled || !firstExam || runExamFlow.isPending}
                onClick={() => firstExam && runExamFlow.mutate(firstExam.id)}
              >
                試験を開始
              </button>
              <p aria-live="polite">
                {lastExamStatus ? labelForStatus(lastExamStatus) : "試験結果はまだありません。"}
              </p>
            </section>
          ) : null}

          {activeRoute === "/admin" ? (
            <section className="page-stack" aria-labelledby="admin-title">
              <PageHeader
                eyebrow="OPERATIONS"
                title="管理"
                description="利用者、学習分析、カリキュラム、機能フラグを確認します。"
                titleId="admin-title"
              />
              {!canAdmin ? <Alert tone="warning">管理画面には管理者権限が必要です。</Alert> : null}
              <div className="card-grid">
                <Metric label="利用者" value={adminUsers.data?.items.length ?? "権限が必要"} />
                <Metric label="学習者" value={analytics.data?.learners ?? "権限が必要"} />
                <Metric
                  label="カリキュラム"
                  value={labelForStatus(curriculumVersions.data?.items[0]?.status)}
                />
              </div>
              <ul className="flag-list" aria-label="機能フラグ">
                {(featureFlags.data?.items ?? []).map((flag) => (
                  <li key={flag.key}>
                    {flag.key}: {flag.enabled ? "有効" : "停止中"}
                  </li>
                ))}
                {!canAdmin ? <li>管理者権限が必要です</li> : null}
              </ul>
            </section>
          ) : null}

          {!NAV_ITEMS.some((item) => item.path === activeRoute) ? (
            <section className="page-stack not-found">
              <PageHeader
                eyebrow="OFF ORBIT"
                title="ページが見つかりません"
                description="URLを確認するか、ナビゲーションから移動してください。"
              />
              <img className="empty-illustration" src={orbitIllustration} alt="" aria-hidden="true" />
              <Link className="button-link" to="/dashboard">
                ダッシュボードへ戻る
              </Link>
            </section>
          ) : null}
        </main>
      </div>
    </div>
  );
}

function BrandLockup({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand-lockup ${compact ? "brand-lockup-compact" : ""}`}>
      <img src={novaMark} width="44" height="44" alt="" aria-hidden="true" />
      <div>
        <p>TAIGA NOVA</p>
        {!compact ? <span>Local Mission Control</span> : null}
      </div>
    </div>
  );
}

function MissionProgressCard({
  progress,
  nextAction,
}: {
  progress: MissionProgress;
  nextAction: string;
}) {
  const percentage = progress.percentage ?? 0;

  return (
    <section
      className={`mission-card mission-${progress.scheduleStatus}`}
      aria-labelledby="mission-progress-title"
    >
      <div className="mission-content">
        <p className="eyebrow">MISSION PROGRESS</p>
        <h2 id="mission-progress-title">学習進捗</h2>
        <div className="mission-number">
          {progress.percentage === null ? "未判定" : `${progress.percentage}%`}
        </div>
        <div
          className="progress-track"
          role="progressbar"
          aria-label="学習進捗"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={percentage}
        >
          <span style={{ width: `${percentage}%` }} />
        </div>
        <div className="mission-meta">
          <StatusBadge status={progress.scheduleStatus} />
          <span>{progress.message}</span>
        </div>
        <p>
          {progress.completed === null
            ? "進捗データが揃うと、完了数と予定との差分を表示します。"
            : `${progress.completed} / ${progress.total} 週が完了しています。`}
        </p>
        <p className="next-action">次の推奨アクション: {nextAction}</p>
      </div>
      <div className="mission-visual">
        {progress.imageSrc ? (
          <img src={progress.imageSrc} alt={progress.imageAlt} width="220" height="220" />
        ) : (
          <img src={orbitIllustration} alt="" aria-hidden="true" width="220" height="160" />
        )}
      </div>
    </section>
  );
}

function FeaturePanel({
  icon: Icon,
  title,
  body,
}: {
  icon: ComponentType<{ size?: number; "aria-hidden"?: boolean }>;
  title: string;
  body: string;
}) {
  return (
    <section className="feature-panel">
      <div className="feature-icon" aria-hidden="true">
        <Icon size={28} />
        <Sparkles size={18} />
      </div>
      <div>
        <h2>{title}</h2>
        <p>{body}</p>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
