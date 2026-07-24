# Resource Usage

## Images

| Image | Size |
|---|---:|
| `app-backend` | 373MB |
| `app-worker` | 373MB |
| `app-frontend` | 688MB |
| `app-runner-controller` | 143MB |
| `postgres:17` | 476MB |

## Containers

| State | Container | CPU | Memory |
|---|---|---:|---:|
| idle-ish | frontend | 0.00% | 336.2MiB |
| idle-ish | worker | 0.00% | 57.44MiB |
| idle-ish | backend | 17.57% | 66.3MiB |
| idle-ish | runner-controller | 0.00% | 4.387MiB |
| idle-ish | postgres | 1.13% | 67.32MiB |
| stress sample | backend | 141.89% | 76.5MiB |
| stress sample | postgres | 0.00% | 65.67MiB |

## Observations

- No container restart was observed.
- Worker logs are bounded to startup messages while idle.
- Frontend image remains large because it is a development Vite container. A production multi-stage static image is deferred until deployment packaging is in scope.
- Backend and worker share the backend image; this keeps consistency but includes dev/test dependencies in the local image.
