# Form and Error Guide

## Active Forms and Controls

| Control | UX rule |
|---|---|
| Local user select | Visible label, accessible name, preserves selected local user |
| Demo submission button | Disabled during pending mutation; success/error feedback in live region |
| Runner action | Disabled when local runner is unavailable or no submission exists |
| Review actions | Approve and revision request are distinct buttons; revision uses danger styling |
| Exam start | Disabled when exam feature is unavailable |

## Errors

- Authentication errors tell the user to choose a valid local user.
- Assignment detail errors mention permission or URL issues without leaking internals.
- Feature-disabled states explain local safety behavior instead of exposing env var names.
- Server and API-level status semantics remain unchanged.

## Deferred

- Error summaries and field-level validation are deferred until multi-field learner submission and
  admin mutation forms are introduced.
- Confirmation dialogs are deferred until there are irreversible destructive mutations in the UI.
