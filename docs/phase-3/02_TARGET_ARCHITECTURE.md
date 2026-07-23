# Target Architecture

## Backend Layers

Transport:

- FastAPI routes parse request models, inject `Principal` and `Session`, and map application
  errors to HTTP responses.

Application services:

- Feature services coordinate SQL reads/writes and call domain policy functions.
- Services own multi-table transaction behavior under the request session boundary.

Domain policy:

- `taiga.authorization` owns reusable role predicates and role requirements.
- `taiga.state_transitions` owns pure status transition decisions.
- `taiga.errors` owns typed application errors and machine-readable codes.

Persistence:

- SQLAlchemy sessions are still request scoped.
- Direct SQL remains inside feature services until broader repository extraction has clear value.

## Frontend Boundaries

- `shared/api/client.ts` remains the only fetch boundary.
- UI can disable unavailable actions, but backend remains authoritative.
- Future status label mapping should live in a shared frontend module when UI copy expands.

## Deferred Architecture

- Full repository pattern extraction.
- Dedicated router modules for every backend feature.
- Generated frontend client.
- Production runner infrastructure and hostile fixture hardening.
