# Seed and Test Data

The local seed imports the read-only curriculum pack and adds deterministic local fixture state.

## Expected Counts

| Entity | Expected |
|---|---:|
| Users | 3 local known users |
| Weeks | 28 |
| Task templates | 196 |
| Task assignments | 196 |
| Exams | 28 |
| Exam variants | 56 |

Seed must be safe to run twice without duplicate rows.

## Verification

`make seed` was executed twice after a fresh migration. The final count query returned:

| Entity | Count |
|---|---:|
| Known local users | 3 |
| Weeks | 28 |
| Task templates | 196 |
| Task assignments | 196 |
| Exams | 28 |
| Exam variants | 56 |
