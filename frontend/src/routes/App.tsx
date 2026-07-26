import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  CalendarDays,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Compass,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Mail,
  Menu,
  ShieldCheck,
  PlayCircle,
  Settings,
  Sparkles,
  Telescope,
  X,
} from "lucide-react";
import { useEffect, useRef, useState, type ComponentType, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import novaMark from "../assets/brand/nova-mark.svg";
import orbitIllustration from "../assets/illustrations/nova-orbit.svg";
import {
  createDemoSubmission,
  createScheduleItem,
  createExamAttempt,
  deleteScheduleItem,
  apiErrorMessage,
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
  getSchedule,
  getScheduleDay,
  getScheduleSummary,
  getStoredLocalUser,
  loginWithPassword,
  logoutSession,
  reviewSubmission,
  runSubmission,
  setStoredLocalUser,
  startExamAttempt,
  submitExamAttempt,
  submitAssignmentEvidence,
  updateScheduleItem,
  type ScheduleDay,
  type ScheduleItem,
  type ScheduleItemInput,
} from "../shared/api/client";
import { formatDate, labelForRole, labelForStatus, shortId } from "../shared/labels";
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
  { path: "/schedule", label: "スケジュール", roles: ["learner", "admin"], icon: CalendarDays },
  { path: "/assignments", label: "課題", roles: ["learner", "admin"], icon: BookOpen },
  { path: "/reviews", label: "レビュー", roles: ["reviewer", "admin"], icon: CheckSquare },
  { path: "/runner", label: "実行環境", roles: ["learner", "admin"], icon: PlayCircle },
  { path: "/exams", label: "試験", roles: ["learner", "admin"], icon: GraduationCap },
  { path: "/admin", label: "管理", roles: ["admin"], icon: Settings },
];
const isProductionBuild = import.meta.env.PROD;
const feExamDate = "2026-10-03";
const piscineStartDate = "2027-03-01";

function routeGroup(pathname: string) {
  if (pathname === "/") return "/dashboard";
  return `/${pathname.split("/").filter(Boolean)[0] ?? "dashboard"}`;
}

function routeTitle(pathname: string) {
  const group = routeGroup(pathname);
  return NAV_ITEMS.find((item) => item.path === group)?.label ?? "ページが見つかりません";
}

function navItemsForEnvironment(isLocalEnvironment: boolean) {
  return isLocalEnvironment
    ? NAV_ITEMS
    : NAV_ITEMS.filter((item) => !["/runner", "/exams"].includes(item.path));
}

export function App() {
  const queryClient = useQueryClient();
  const location = useLocation();
  const navigate = useNavigate();
  const activeRoute = routeGroup(location.pathname);
  const routeAssignmentId = location.pathname.match(/^\/assignments\/([^/]+)/)?.[1] ?? null;
  const previousPathRef = useRef(location.pathname);
  const menuButtonRef = useRef<HTMLButtonElement | null>(null);
  const sidebarRef = useRef<HTMLElement | null>(null);
  const [isMobileNavOpen, setMobileNavOpen] = useState(false);
  const [isNarrowViewport, setNarrowViewport] = useState(false);
  const [localUser, setLocalUser] = useState(getStoredLocalUser());
  const [selectedAssignmentId, setSelectedAssignmentId] = useState<string | null>(routeAssignmentId);
  const [lastSubmissionId, setLastSubmissionId] = useState<string | null>(null);
  const [lastRunnerStatus, setLastRunnerStatus] = useState<string | null>(null);
  const [lastReviewResult, setLastReviewResult] = useState<string | null>(null);
  const [lastExamStatus, setLastExamStatus] = useState<string | null>(null);
  const [scheduleMonth, setScheduleMonth] = useState(() => startOfMonth(todayIsoDate()));
  const [selectedScheduleDate, setSelectedScheduleDate] = useState(todayIsoDate());
  const [scheduleForm, setScheduleForm] = useState<ScheduleFormState>(() =>
    emptyScheduleForm(todayIsoDate()),
  );
  const [assignmentForm, setAssignmentForm] = useState({
    repositoryUrl: "",
    commitHash: "",
    note: "",
    attachments: [] as File[],
  });
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");

  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const me = useQuery({ queryKey: ["me", localUser], queryFn: getMe });
  const isLocalEnvironment = !isProductionBuild && health.data?.app_env !== "production";
  const isSignedIn = me.isSuccess;
  const canReview = me.data?.role === "reviewer" || me.data?.role === "admin";
  const canAdmin = me.data?.role === "admin";
  const canSubmitAssignment = me.data?.role === "learner";
  const login = useMutation({
    mutationFn: loginWithPassword,
    onSuccess: async () => {
      setLoginPassword("");
      await queryClient.invalidateQueries({ queryKey: ["me"] });
    },
  });
  const logout = useMutation({
    mutationFn: logoutSession,
    onSuccess: async () => {
      await queryClient.clear();
      window.location.assign("/");
    },
  });
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
  const scheduleRange = calendarRange(scheduleMonth);
  const schedule = useQuery({
    queryKey: ["schedule", localUser, scheduleRange.from, scheduleRange.to],
    queryFn: () => getSchedule(scheduleRange.from, scheduleRange.to),
    enabled: isSignedIn && activeRoute === "/schedule",
  });
  const scheduleDay = useQuery({
    queryKey: ["schedule-day", localUser, selectedScheduleDate],
    queryFn: () => getScheduleDay(selectedScheduleDate),
    enabled: isSignedIn && activeRoute === "/schedule",
  });
  const scheduleSummary = useQuery({
    queryKey: ["schedule-summary", localUser],
    queryFn: getScheduleSummary,
    enabled: isSignedIn && (activeRoute === "/dashboard" || activeRoute === "/schedule"),
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
    enabled: canAdmin && isLocalEnvironment,
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
  const submitEvidence = useMutation({
    mutationFn: ({ assignmentId }: { assignmentId: string }) =>
      submitAssignmentEvidence(assignmentId, assignmentForm),
    onSuccess: async (submission) => {
      setLastSubmissionId(submission.id);
      setAssignmentForm({ repositoryUrl: "", commitHash: "", note: "", attachments: [] });
      await queryClient.invalidateQueries({ queryKey: ["assignments", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["assignment-detail", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-summary", localUser] });
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
  const saveScheduleItem = useMutation({
    mutationFn: (input: ScheduleItemInput & { id?: string }) => {
      const { id, ...payload } = input;
      return id ? updateScheduleItem(id, payload) : createScheduleItem(payload);
    },
    onSuccess: async () => {
      setScheduleForm(emptyScheduleForm(selectedScheduleDate));
      await queryClient.invalidateQueries({ queryKey: ["schedule", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-day", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-summary", localUser] });
    },
  });
  const cancelScheduleItem = useMutation({
    mutationFn: (id: string) =>
      updateScheduleItem(id, { statusOverride: "cancelled", isRequired: false }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["schedule", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-day", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-summary", localUser] });
    },
  });
  const removeScheduleItem = useMutation({
    mutationFn: deleteScheduleItem,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["schedule", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-day", localUser] });
      await queryClient.invalidateQueries({ queryKey: ["schedule-summary", localUser] });
    },
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

  function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ email: loginEmail.trim(), password: loginPassword });
  }

  function openAssignment(assignmentId: string) {
    setSelectedAssignmentId(assignmentId);
    navigate(`/assignments/${assignmentId}`);
  }

  function openScheduleAssignment(item: ScheduleItem) {
    if (!item.assignmentId) {
      return;
    }
    setSelectedAssignmentId(item.assignmentId);
    navigate(`/assignments/${item.assignmentId}`);
  }

  function loadScheduleItemForEdit(item: ScheduleItem) {
    setScheduleForm({
      id: item.id,
      date: item.date,
      title: item.title,
      description: item.description,
      itemType: item.itemType,
      priority: String(item.priority),
      dueAt: item.dueAt ?? "",
      sourceUrl: item.sourceUrl ?? "",
      isRequired: item.isRequired,
      statusOverride: item.displayStatus === "cancelled" ? "cancelled" : "",
      deliverables: arrayMetadata(item.metadata.deliverables).join("\n"),
      acceptanceCriteria: arrayMetadata(item.metadata.acceptanceCriteria).join("\n"),
      allowedEvidenceTypes: arrayMetadata(item.metadata.allowedEvidenceTypes).join(", "),
    });
  }

  function submitScheduleForm() {
    const payload = formToScheduleInput(scheduleForm);
    if (!payload.title || !payload.date || !payload.itemType) {
      return;
    }
    saveScheduleItem.mutate({ ...payload, id: scheduleForm.id || undefined });
  }

  function submitAssignmentForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selectedAssignment ||
      (!assignmentForm.note.trim() &&
        !assignmentForm.repositoryUrl.trim() &&
        assignmentForm.attachments.length === 0)
    ) {
      return;
    }
    submitEvidence.mutate({ assignmentId: selectedAssignment });
  }

  const firstAssignment = assignments.data?.items[0];
  const firstExam = exams.data?.items[0];
  const runnerDisabled = health.data?.runner_enabled === false;
  const examDisabled = !examEnabled;
  const availableNav = navItemsForEnvironment(isLocalEnvironment);
  const visibleNav = availableNav.filter((item) => item.roles.includes(me.data?.role ?? "learner"));
  const daysUntilFeExam = daysUntil(feExamDate);
  const daysUntilPiscine = scheduleSummary.data?.daysUntilPiscine ?? daysUntil(piscineStartDate);

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
    document.body.style.overflow = "hidden";
    const focusableElements = () =>
      Array.from(
        sidebarRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
    focusableElements()[0]?.focus();

    function handleDrawerKeydown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMobileNavOpen(false);
        menuButtonRef.current?.focus();
      }
      if (event.key !== "Tab") {
        return;
      }
      const focusable = focusableElements();
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) {
        return;
      }
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    window.addEventListener("keydown", handleDrawerKeydown);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", handleDrawerKeydown);
    };
  }, [isMobileNavOpen]);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 1023px)");
    const updateNarrowViewport = () => setNarrowViewport(media.matches);
    updateNarrowViewport();
    media.addEventListener("change", updateNarrowViewport);
    return () => media.removeEventListener("change", updateNarrowViewport);
  }, []);

  if (!isLocalEnvironment && !isSignedIn) {
    return (
      <main className="auth-screen" aria-labelledby="login-title">
        <section className="auth-panel">
          <div className="auth-brand">
            <img src={novaMark} alt="" />
            <div>
              <p className="eyebrow">TAIGA NOVA</p>
              <h1 id="login-title">ログイン</h1>
            </div>
          </div>
          <form className="auth-form" onSubmit={submitLogin}>
            <label htmlFor="login-email">メールアドレス</label>
            <div className="input-with-icon">
              <Mail aria-hidden size={18} />
              <input
                id="login-email"
                name="email"
                type="email"
                autoComplete="username"
                value={loginEmail}
                onChange={(event) => setLoginEmail(event.target.value)}
                required
              />
            </div>
            <label htmlFor="login-password">パスワード</label>
            <div className="input-with-icon">
              <ShieldCheck aria-hidden size={18} />
              <input
                id="login-password"
                name="password"
                type="password"
                autoComplete="current-password"
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
                required
              />
            </div>
            {login.isError ? <Alert tone="danger">{apiErrorMessage(login.error)}</Alert> : null}
            <button className="primary-action auth-submit" type="submit" disabled={login.isPending}>
              ログイン
            </button>
          </form>
        </section>
      </main>
    );
  }

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

      <aside
        id="site-sidebar"
        ref={sidebarRef}
        className="sidebar"
        aria-label="TAIGA NOVA ナビゲーション"
        aria-hidden={isNarrowViewport && !isMobileNavOpen ? "true" : undefined}
        {...(isNarrowViewport && !isMobileNavOpen ? { inert: true } : {})}
      >
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
        {isLocalEnvironment ? (
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
        ) : (
          <section className="login-panel" aria-label="ログイン中の利用者">
            <h2>ログイン中</h2>
            <p>{me.data ? `${me.data.displayName} · ${labelForRole(me.data.role)}` : "Cloudflare Access"}</p>
            <button
              className="button-link secondary logout-link"
              type="button"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
            >
              <LogOut aria-hidden size={18} />
              ログアウト
            </button>
          </section>
        )}
      </aside>

      <div className="main-shell">
        {isLocalEnvironment ? (
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
        ) : null}

        <main id="main-content" className="main-content" tabIndex={-1}>
          {health.isPending ? (
            <Alert tone="info">サーバーを起動しています。初回のみ数十秒かかる場合があります。</Alert>
          ) : null}
          {health.isError ? (
            <Alert tone="warning">
              {apiErrorMessage(health.error)}
              <button type="button" onClick={() => health.refetch()}>
                再試行
              </button>
            </Alert>
          ) : null}
          {me.isError ? (
            <Alert tone="danger">{apiErrorMessage(me.error)}</Alert>
          ) : null}
          {activeRoute === "/dashboard" ? (
            <section className="page-stack dashboard-grid" aria-labelledby="dashboard-title">
              <PageHeader
                eyebrow="MISSION CONTROL"
                title="ダッシュボード"
                description="学習の現在地、次に進む課題、運用状態を確認できます。"
                titleId="dashboard-title"
              />
              {dashboard.isLoading || progress.isLoading || scheduleSummary.isLoading ? <LoadingState /> : null}
              <MissionReadinessCard
                daysUntilFeExam={daysUntilFeExam}
                daysUntilPiscine={daysUntilPiscine}
                overdueCount={scheduleSummary.data?.learnerOverdueCount ?? 0}
                reviewWaitingCount={scheduleSummary.data?.reviewWaitingCount ?? 0}
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
                <Metric label="基本情報まで" value={`${daysUntilFeExam}日`} />
                <Metric label="Piscineまで" value={`${daysUntilPiscine}日`} />
              </div>
              <Alert tone="info">TAIGA NOVAは直接URL、ブラウザ更新、戻る操作に対応しています。</Alert>
            </section>
          ) : null}

          {activeRoute === "/schedule" ? (
            <section className="page-stack" aria-labelledby="schedule-title">
              <PageHeader
                eyebrow="DAILY CALENDAR"
                title="スケジュール"
                description="日単位の予定、未完了、遅延、重要日程を確認できます。"
                titleId="schedule-title"
              />
              {schedule.isLoading || scheduleDay.isLoading || scheduleSummary.isLoading ? (
                <LoadingState label="スケジュールを読み込み中です" />
              ) : null}
              {schedule.isError || scheduleDay.isError || scheduleSummary.isError ? (
                <Alert tone="danger">スケジュールを読み込めません。</Alert>
              ) : null}
              <div className="schedule-summary-grid" aria-label="スケジュール概要">
                <Metric label="今日の件数" value={scheduleSummary.data?.todayCount ?? 0} />
                <Metric label="遅延" value={scheduleSummary.data?.learnerOverdueCount ?? 0} />
                <Metric label="レビュー待ち" value={scheduleSummary.data?.reviewWaitingCount ?? 0} />
                <Metric label="Piscineまで" value={`${scheduleSummary.data?.daysUntilPiscine ?? 0}日`} />
              </div>
              <div className="schedule-toolbar">
                <button
                  type="button"
                  className="icon-text-button"
                  onClick={() => setScheduleMonth(addMonths(scheduleMonth, -1))}
                  aria-label="前月へ"
                >
                  <ChevronLeft aria-hidden size={18} />
                  前月
                </button>
                <strong>{formatMonthLabel(scheduleMonth)}</strong>
                <button
                  type="button"
                  className="icon-text-button"
                  onClick={() => setScheduleMonth(addMonths(scheduleMonth, 1))}
                  aria-label="次月へ"
                >
                  次月
                  <ChevronRight aria-hidden size={18} />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const today = todayIsoDate();
                    setScheduleMonth(startOfMonth(today));
                    setSelectedScheduleDate(today);
                  }}
                >
                  今日
                </button>
              </div>
              {scheduleSummary.data?.nextImportantDate ? (
                <Alert tone="info">
                  次の重要日程: {formatDate(scheduleSummary.data.nextImportantDate)}{" "}
                  {scheduleSummary.data.nextImportantTitle}
                </Alert>
              ) : null}
              <div className="calendar-legend" aria-label="カレンダー凡例">
                <span data-tone="important">重要日</span>
                <span data-tone="overdue">遅延</span>
                <span data-tone="review">レビュー待ち</span>
                <span data-tone="approved">完了</span>
              </div>
              <ScheduleCalendar
                month={scheduleMonth}
                days={schedule.data?.days ?? []}
                selectedDate={selectedScheduleDate}
                onSelectDate={(date) => {
                  setSelectedScheduleDate(date);
                  setScheduleForm((current) =>
                    current.id ? current : { ...current, date },
                  );
                }}
              />
              <ScheduleDayDetail
                day={scheduleDay.data}
                onOpenAssignment={openScheduleAssignment}
                canAdmin={canAdmin}
                onEditItem={loadScheduleItemForEdit}
                onCancelItem={(id) => cancelScheduleItem.mutate(id)}
                onDeleteItem={(id) => removeScheduleItem.mutate(id)}
              />
              {canAdmin ? (
                <ScheduleAdminPanel
                  form={scheduleForm}
                  selectedDate={selectedScheduleDate}
                  isSaving={saveScheduleItem.isPending}
                  isMutating={cancelScheduleItem.isPending || removeScheduleItem.isPending}
                  onChange={setScheduleForm}
                  onSubmit={submitScheduleForm}
                  onReset={() => setScheduleForm(emptyScheduleForm(selectedScheduleDate))}
                />
              ) : null}
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
                <div className="assignment-detail-header">
                  <div>
                    <strong>{assignmentDetail.data?.assignment.title ?? "課題を選択してください"}</strong>
                    {assignmentDetail.data?.goal ? <p>{assignmentDetail.data.goal}</p> : null}
                  </div>
                  <StatusBadge status={assignmentDetail.data?.assignment.status} />
                </div>
                {assignmentDetail.isError ? (
                  <Alert tone="danger">課題を読み込めません。権限またはURLを確認してください。</Alert>
                ) : null}
                {assignmentDetail.data ? (
                  <div className="assignment-detail-grid">
                    <section className="assignment-panel" aria-labelledby="assignment-steps-title">
                      <h2 id="assignment-steps-title">やること</h2>
                      <ol className="plain-list">
                        {assignmentDetail.data.instructions.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ol>
                    </section>
                    <section className="assignment-panel" aria-labelledby="assignment-materials-title">
                      <h2 id="assignment-materials-title">教材</h2>
                      <div className="material-list">
                        {assignmentDetail.data.materials.map((material) => (
                          <article className="material-item" key={material.id}>
                            <div>
                              <strong>{material.title}</strong>
                              <span>
                                {material.provider} · {material.required ? "必須" : "参考"}
                              </span>
                            </div>
                            {material.url ? (
                              <a href={material.url} target="_blank" rel="noreferrer">
                                開く
                              </a>
                            ) : (
                              <span>手元教材</span>
                            )}
                          </article>
                        ))}
                      </div>
                    </section>
                    <section className="assignment-panel" aria-labelledby="assignment-submit-title">
                      <h2 id="assignment-submit-title">提出方法</h2>
                      <ol className="plain-list">
                        {assignmentDetail.data.submissionGuide.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ol>
                      <div className="artifact-list" aria-label="提出物">
                        <strong>提出物</strong>
                        {assignmentDetail.data.requiredArtifacts.length > 0 ? (
                          assignmentDetail.data.requiredArtifacts.map((artifact) => (
                            <span key={`${artifact.path}-${artifact.kind}`}>
                              {artifact.path} ({artifact.kind})
                            </span>
                          ))
                        ) : (
                          <span>回答メモまたはGitHub URL</span>
                        )}
                      </div>
                    </section>
                    <section className="assignment-panel" aria-labelledby="assignment-review-title">
                      <h2 id="assignment-review-title">合格条件</h2>
                      <ul className="plain-list">
                        {assignmentDetail.data.approvalCriteria.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                      <p>提出履歴: {assignmentDetail.data.submissions.length}件</p>
                    </section>
                  </div>
                ) : null}
              </div>
              {canSubmitAssignment && assignmentDetail.data ? (
                <form className="submission-form" onSubmit={submitAssignmentForm}>
                  <div className="section-heading">
                    <p className="eyebrow">SUBMIT</p>
                    <h2>回答を提出</h2>
                  </div>
                  <label>
                    GitHub URL（任意）
                    <input
                      type="url"
                      value={assignmentForm.repositoryUrl}
                      placeholder="https://github.com/..."
                      onChange={(event) =>
                        setAssignmentForm((current) => ({
                          ...current,
                          repositoryUrl: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label>
                    Commit hash（任意）
                    <input
                      value={assignmentForm.commitHash}
                      placeholder="abc123..."
                      onChange={(event) =>
                        setAssignmentForm((current) => ({
                          ...current,
                          commitHash: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label>
                    回答メモ
                    <textarea
                      required={!assignmentForm.repositoryUrl.trim()}
                      value={assignmentForm.note}
                      placeholder="やったこと、結果、詰まった点、スクリーンショットの場所などを書く"
                      onChange={(event) =>
                        setAssignmentForm((current) => ({
                          ...current,
                          note: event.target.value,
                        }))
                      }
                    />
                  </label>
                  <label>
                    写真・ファイル添付（任意）
                    <input
                      type="file"
                      accept="image/*,.md,.txt,.zip"
                      capture="environment"
                      multiple
                      onChange={(event) =>
                        setAssignmentForm((current) => ({
                          ...current,
                          attachments: Array.from(event.target.files ?? []),
                        }))
                      }
                    />
                  </label>
                  {assignmentForm.attachments.length > 0 ? (
                    <div className="attachment-list" aria-label="選択中の添付">
                      {assignmentForm.attachments.map((file) => (
                        <span key={`${file.name}-${file.size}`}>
                          {file.name} · {formatBytes(file.size)}
                        </span>
                      ))}
                    </div>
                  ) : null}
                  <div className="button-row">
                    <button
                      type="submit"
                      className="primary-action"
                      disabled={
                        submitEvidence.isPending ||
                        (!assignmentForm.note.trim() &&
                          !assignmentForm.repositoryUrl.trim() &&
                          assignmentForm.attachments.length === 0)
                      }
                    >
                      提出する
                    </button>
                  </div>
                  <p aria-live="polite">
                    {lastSubmissionId
                      ? `提出しました。レビュー待ちです: ${shortId(lastSubmissionId)}`
                      : submitEvidence.error
                        ? "提出に失敗しました。入力内容を確認してください。"
                        : "回答メモ、GitHub URL、写真添付のどれかを入れて提出できます。"}
                  </p>
                </form>
              ) : null}
              {isLocalEnvironment ? (
                <>
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
                </>
              ) : null}
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
                    {submission.repositoryUrl ? (
                      <a href={submission.repositoryUrl} target="_blank" rel="noreferrer">
                        GitHub URLを開く
                      </a>
                    ) : null}
                    {submission.submissionNote ? (
                      <p className="submission-note-preview">{submission.submissionNote}</p>
                    ) : null}
                    {(submission.artifactNames ?? []).length > 0 ? (
                      <p>添付: {(submission.artifactNames ?? []).join("、")}</p>
                    ) : null}
                    {(submission.artifactLinks ?? []).length > 0 ? (
                      <div className="attachment-link-list" aria-label="提出添付">
                        {(submission.artifactLinks ?? []).map((artifact) => (
                          <a
                            key={artifact.id}
                            href={`/api/v1/submission-artifacts/${artifact.id}/content`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            {artifact.originalName}
                          </a>
                        ))}
                      </div>
                    ) : null}
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

          {isLocalEnvironment && activeRoute === "/runner" ? (
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

          {isLocalEnvironment && activeRoute === "/exams" ? (
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
              {isLocalEnvironment ? (
                <ul className="flag-list" aria-label="機能フラグ">
                  {(featureFlags.data?.items ?? []).map((flag) => (
                    <li key={flag.key}>
                      {flag.key}: {flag.enabled ? "有効" : "停止中"}
                    </li>
                  ))}
                  {!canAdmin ? <li>管理者権限が必要です</li> : null}
                </ul>
              ) : null}
            </section>
          ) : null}

          {!availableNav.some((item) => item.path === activeRoute) ? (
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
        {!compact ? <span>Mission Control</span> : null}
      </div>
    </div>
  );
}

const weekdayLabels = ["月", "火", "水", "木", "金", "土", "日"];

const scheduleStatusLabels: Record<string, string> = {
  learner_overdue: "遅延",
  review_overdue: "レビュー期限超過",
  revision_requested: "修正",
  not_submitted: "未提出",
  in_progress: "進行中",
  review_waiting: "レビュー待ち",
  not_started: "未開始",
  approved: "合格",
  cancelled: "対象外",
  event: "予定",
};

function todayIsoDate() {
  const formatter = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
  return formatter.format(new Date());
}

function daysUntil(targetIsoDate: string) {
  const today = new Date(`${todayIsoDate()}T00:00:00+09:00`);
  const target = new Date(`${targetIsoDate}T00:00:00+09:00`);
  return Math.max(0, Math.ceil((target.getTime() - today.getTime()) / 86_400_000));
}

function startOfMonth(isoDate: string) {
  return `${isoDate.slice(0, 7)}-01`;
}

function addMonths(monthIso: string, amount: number) {
  const [year, month] = monthIso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1 + amount, 1));
  return date.toISOString().slice(0, 10);
}

function isoFromDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function calendarRange(monthIso: string) {
  const [year, month] = monthIso.split("-").map(Number);
  const first = new Date(Date.UTC(year, month - 1, 1));
  const firstMondayOffset = (first.getUTCDay() + 6) % 7;
  const from = new Date(first);
  from.setUTCDate(first.getUTCDate() - firstMondayOffset);
  const last = new Date(Date.UTC(year, month, 0));
  const lastSundayOffset = 6 - ((last.getUTCDay() + 6) % 7);
  const to = new Date(last);
  to.setUTCDate(last.getUTCDate() + lastSundayOffset);
  return { from: isoFromDate(from), to: isoFromDate(to) };
}

function formatMonthLabel(monthIso: string) {
  const [year, month] = monthIso.split("-");
  return `${year}年${Number(month)}月`;
}

function isSameMonth(dateIso: string, monthIso: string) {
  return dateIso.slice(0, 7) === monthIso.slice(0, 7);
}

function ScheduleCalendar({
  month,
  days,
  selectedDate,
  onSelectDate,
}: {
  month: string;
  days: ScheduleDay[];
  selectedDate: string;
  onSelectDate: (date: string) => void;
}) {
  return (
    <section className="schedule-calendar" aria-label="月表示カレンダー">
      <div className="calendar-weekdays" aria-hidden="true">
        {weekdayLabels.map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>
      <div className="calendar-grid">
        {days.map((day) => {
          const label = scheduleStatusLabels[day.representativeStatus] ?? "予定";
          const importantItems = day.items.filter(isImportantScheduleItem);
          const visibleItems = [...importantItems, ...day.items.filter((item) => !isImportantScheduleItem(item))];
          return (
            <button
              key={day.date}
              type="button"
              className="calendar-cell"
              data-status={day.representativeStatus}
              data-important={importantItems.length > 0 ? "true" : undefined}
              data-selected={day.date === selectedDate ? "true" : undefined}
              data-muted={!isSameMonth(day.date, month) ? "true" : undefined}
              onClick={() => onSelectDate(day.date)}
              aria-pressed={day.date === selectedDate}
            >
              <span className="calendar-day-number">{Number(day.date.slice(8, 10))}</span>
              {day.isToday ? <span className="today-label">今日</span> : null}
              <span className="calendar-status-text">{label}</span>
              <span className="calendar-count">{day.items.length}件</span>
              {visibleItems.slice(0, 2).map((item) => (
                <span
                  className="calendar-chip"
                  data-important={isImportantScheduleItem(item) ? "true" : undefined}
                  key={item.id}
                >
                  {item.title}
                </span>
              ))}
            </button>
          );
        })}
      </div>
    </section>
  );
}

function ScheduleDayDetail({
  day,
  onOpenAssignment,
  canAdmin,
  onEditItem,
  onCancelItem,
  onDeleteItem,
}: {
  day?: ScheduleDay;
  onOpenAssignment: (item: ScheduleItem) => void;
  canAdmin: boolean;
  onEditItem: (item: ScheduleItem) => void;
  onCancelItem: (id: string) => void;
  onDeleteItem: (id: string) => void;
}) {
  const items = day?.items ?? [];
  const topPriority = items.find((item) => item.isRequired) ?? items[0];
  return (
    <section className="schedule-detail-panel" aria-labelledby="schedule-detail-title">
      <div className="section-heading">
        <p className="eyebrow">DAY DETAIL</p>
        <h2 id="schedule-detail-title">
          {day ? formatDate(day.date) : "日付を選択してください"}
        </h2>
      </div>
      {topPriority ? (
        <div className="priority-strip">
          <span>最優先</span>
          <strong>{topPriority.title}</strong>
          <StatusBadge status={topPriority.displayStatus} />
        </div>
      ) : (
        <EmptyState title="この日の予定はありません。" />
      )}
      <div className="schedule-item-list">
        {items.map((item) => {
          const deliverables = arrayMetadata(item.metadata.deliverables);
          const criteria = arrayMetadata(item.metadata.acceptanceCriteria);
          const evidence = arrayMetadata(item.metadata.allowedEvidenceTypes);
          return (
            <article
              className="schedule-item-card"
              key={item.id}
              data-status={item.displayStatus}
              data-important={isImportantScheduleItem(item) ? "true" : undefined}
            >
              <div className="schedule-item-heading">
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.itemType}</span>
                </div>
                <StatusBadge status={item.displayStatus} />
              </div>
              <p>{item.description}</p>
              <dl className="schedule-item-meta">
                <div>
                  <dt>期限</dt>
                  <dd>{item.dueAt ? formatDate(item.dueAt.slice(0, 10)) : "指定なし"}</dd>
                </div>
                <div>
                  <dt>遅延</dt>
                  <dd>{item.isOverdue ? `${item.overdueDays}日` : "なし"}</dd>
                </div>
                <div>
                  <dt>提出</dt>
                  <dd>{evidence.join(" / ") || "記録"}</dd>
                </div>
              </dl>
              {deliverables.length > 0 ? <p>成果物: {deliverables.join("、")}</p> : null}
              {criteria.length > 0 ? <p>合格条件: {criteria.join("、")}</p> : null}
              <div className="button-row">
                {item.assignmentId ? (
                  <button type="button" onClick={() => onOpenAssignment(item)}>
                    課題詳細へ
                  </button>
                ) : null}
                {item.sourceUrl ? (
                  <a className="button-link secondary" href={item.sourceUrl} target="_blank" rel="noreferrer">
                    根拠URL
                  </a>
                ) : null}
                {canAdmin ? (
                  <>
                    <button type="button" onClick={() => onEditItem(item)}>
                      編集に読み込む
                    </button>
                    <button type="button" onClick={() => onCancelItem(item.id)}>
                      対象外
                    </button>
                    <button type="button" className="danger-action" onClick={() => onDeleteItem(item.id)}>
                      削除
                    </button>
                  </>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

type ScheduleFormState = {
  id: string;
  date: string;
  title: string;
  description: string;
  itemType: string;
  priority: string;
  dueAt: string;
  sourceUrl: string;
  isRequired: boolean;
  statusOverride: string;
  deliverables: string;
  acceptanceCriteria: string;
  allowedEvidenceTypes: string;
};

function emptyScheduleForm(date: string): ScheduleFormState {
  return {
    id: "",
    date,
    title: "",
    description: "",
    itemType: "milestone",
    priority: "50",
    dueAt: "",
    sourceUrl: "",
    isRequired: true,
    statusOverride: "",
    deliverables: "",
    acceptanceCriteria: "",
    allowedEvidenceTypes: "text",
  };
}

function lines(value: string) {
  return value
    .split(/\n|,/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function formToScheduleInput(form: ScheduleFormState): ScheduleItemInput {
  const metadata = {
    deliverables: lines(form.deliverables),
    acceptanceCriteria: lines(form.acceptanceCriteria),
    allowedEvidenceTypes: lines(form.allowedEvidenceTypes),
    nextAction: "Shomaが確認し、必要なら予定を調整する",
  };
  return {
    date: form.date,
    title: form.title,
    description: form.description,
    itemType: form.itemType,
    priority: Number(form.priority),
    dueAt: form.dueAt || null,
    sourceUrl: form.sourceUrl || null,
    isRequired: form.isRequired,
    statusOverride: form.statusOverride || null,
    metadata,
  };
}

function ScheduleAdminPanel({
  form,
  selectedDate,
  isSaving,
  isMutating,
  onChange,
  onSubmit,
  onReset,
}: {
  form: ScheduleFormState;
  selectedDate: string;
  isSaving: boolean;
  isMutating: boolean;
  onChange: (form: ScheduleFormState) => void;
  onSubmit: () => void;
  onReset: () => void;
}) {
  function update<K extends keyof ScheduleFormState>(key: K, value: ScheduleFormState[K]) {
    onChange({ ...form, [key]: value });
  }

  return (
    <section className="schedule-admin-panel" aria-labelledby="schedule-admin-title">
      <div className="section-heading">
        <p className="eyebrow">SHOMA CONTROL</p>
        <h2 id="schedule-admin-title">スケジュール管理</h2>
      </div>
      <div className="schedule-admin-grid">
        <label>
          日付
          <input type="date" value={form.date || selectedDate} onChange={(event) => update("date", event.target.value)} />
        </label>
        <label>
          種別
          <select value={form.itemType} onChange={(event) => update("itemType", event.target.value)}>
            {["assignment", "exam", "application", "orientation", "housing", "finance", "travel", "piscine", "milestone", "rest", "review"].map((type) => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </label>
        <label>
          優先度
          <input type="number" min="1" max="100" value={form.priority} onChange={(event) => update("priority", event.target.value)} />
        </label>
        <label>
          状態
          <select value={form.statusOverride} onChange={(event) => update("statusOverride", event.target.value)}>
            <option value="">自動判定</option>
            <option value="not_started">未開始</option>
            <option value="in_progress">進行中</option>
            <option value="submitted">レビュー待ち</option>
            <option value="revision_requested">修正依頼</option>
            <option value="approved">合格</option>
            <option value="cancelled">対象外</option>
          </select>
        </label>
      </div>
      <label>
        タイトル
        <input value={form.title} onChange={(event) => update("title", event.target.value)} />
      </label>
      <label>
        説明
        <textarea value={form.description} onChange={(event) => update("description", event.target.value)} />
      </label>
      <div className="schedule-admin-grid">
        <label>
          期限
          <input value={form.dueAt} placeholder="2026-09-30T23:59:00+09:00" onChange={(event) => update("dueAt", event.target.value)} />
        </label>
        <label>
          根拠URL
          <input value={form.sourceUrl} onChange={(event) => update("sourceUrl", event.target.value)} />
        </label>
      </div>
      <label>
        成果物
        <textarea value={form.deliverables} onChange={(event) => update("deliverables", event.target.value)} />
      </label>
      <label>
        合格条件
        <textarea value={form.acceptanceCriteria} onChange={(event) => update("acceptanceCriteria", event.target.value)} />
      </label>
      <label>
        証跡種別
        <input value={form.allowedEvidenceTypes} onChange={(event) => update("allowedEvidenceTypes", event.target.value)} />
      </label>
      <label className="checkbox-row">
        <input type="checkbox" checked={form.isRequired} onChange={(event) => update("isRequired", event.target.checked)} />
        必須予定として扱う
      </label>
      <div className="button-row">
        <button type="button" className="primary-action" disabled={isSaving || !form.title} onClick={onSubmit}>
          {form.id ? "更新" : "追加"}
        </button>
        <button type="button" disabled={isSaving || isMutating} onClick={onReset}>
          入力をクリア
        </button>
      </div>
      <p aria-live="polite">{isSaving ? "保存中です" : form.id ? "既存予定を編集中です" : "新しい予定を追加できます。"}</p>
    </section>
  );
}

function arrayMetadata(value: unknown) {
  return Array.isArray(value) ? value.map(String) : [];
}

function formatBytes(size: number) {
  if (size < 1024 * 1024) {
    return `${Math.max(1, Math.round(size / 1024))}KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)}MB`;
}

function isImportantScheduleItem(item: ScheduleItem) {
  return (
    item.priority >= 80 ||
    item.itemType === "milestone" ||
    item.itemType === "exam" ||
    item.itemType === "piscine" ||
    Boolean(item.milestoneKey)
  );
}

function MissionReadinessCard({
  daysUntilFeExam,
  daysUntilPiscine,
  overdueCount,
  reviewWaitingCount,
  nextAction,
}: {
  daysUntilFeExam: number;
  daysUntilPiscine: number;
  overdueCount: number;
  reviewWaitingCount: number;
  nextAction: string;
}) {
  return (
    <section
      className="mission-card readiness-card"
      aria-labelledby="mission-progress-title"
    >
      <div className="mission-content">
        <p className="eyebrow">NEXT DEADLINE</p>
        <h2 id="mission-progress-title">基本情報試験まで</h2>
        <div className="mission-number">{daysUntilFeExam}日</div>
        <p>試験日: {formatDate(feExamDate)}</p>
        <p className="next-action">次の推奨アクション: {nextAction}</p>
      </div>
      <div className="readiness-metrics" aria-label="運用指標">
        <div>
          <span>Piscineまで</span>
          <strong>{daysUntilPiscine}日</strong>
        </div>
        <div>
          <span>遅延</span>
          <strong>{overdueCount}</strong>
        </div>
        <div>
          <span>レビュー待ち</span>
          <strong>{reviewWaitingCount}</strong>
        </div>
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
