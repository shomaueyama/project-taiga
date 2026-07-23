# Component and State Guide

## Shared Components

- `PageHeader`: eyebrow, single page title, description, optional title id.
- `StatusBadge`: maps internal status to Japanese text and state tone.
- `LoadingState`: announced loading message with `role="status"`.
- `EmptyState`: explicit no-data state.
- `Alert`: info, warning, and danger messages.

## State Patterns

- Loading appears near the data region being loaded.
- Empty states distinguish no work from inaccessible work.
- Success feedback remains visible in a polite live region.
- Error feedback uses Japanese and avoids internal exception detail.
- Pending mutations disable the relevant button to prevent duplicate submission.
- Feature-disabled states include explanatory text and disabled controls.

## Boundaries

- Shared UI components do not import business API clients.
- Domain terminology and formatting live in `frontend/src/shared/labels.ts`.
- Components do not change backend authorization, state, or contract behavior.
