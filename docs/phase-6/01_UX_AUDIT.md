# UX Audit

## Learner

| Screen | Purpose | Primary action | Findings | Fix |
|---|---|---|---|---|
| Dashboard | Show today's learning state | Choose next workflow | Single-screen MVP made location unclear | Added `/dashboard` route, Japanese title, summary, metrics |
| Assignments | Review task and submission state | Submit demo answer | Assignment detail was implicit state | Added `/assignments` and `/assignments/:assignmentId` handling |
| Submission | Create immutable submission | Submit once | Mutation feedback was terse | Added live success/error feedback and pending disabled guard |
| Runner | Show local execution availability | Run latest submission when enabled | Disabled state could look like a failure | Added Japanese safety explanation and disabled button |
| Exam | Show exam availability | Start exam when enabled | Disabled state exposed technical feature flag concept | Added local-environment explanation without env var names |

## Reviewer

| Screen | Purpose | Primary action | Findings | Fix |
|---|---|---|---|---|
| Review queue | Review pending submissions | Approve or request revision | Actions needed clear status feedback | Added `/reviews`, status badges, live review result |
| Empty queue | Confirm no pending work | None | Empty state needed explicit text | Added empty state component |

## Admin

| Screen | Purpose | Primary action | Findings | Fix |
|---|---|---|---|---|
| Admin overview | Inspect users, analytics, curriculum, flags | Read operational state | Admin-only data was mixed with other flows | Added `/admin`, role-aware navigation, safe unauthorized message |

## Shared

- Navigation: added role-aware links and `aria-current`.
- Header: kept product identity separate from per-page `h1`.
- Login: visible label and accessible select name use Japanese.
- Loading: loading state is announced with `role="status"`.
- Errors: shared alert patterns use Japanese, do not expose traceback details.
- Mobile: sidebar stacks above content and list rows stack on narrow widths.
