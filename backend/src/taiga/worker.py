import time

from sqlalchemy.exc import SQLAlchemyError

from taiga.config import get_settings
from taiga.infrastructure.database import SessionLocal
from taiga.runner_jobs import process_next_runner_job


def main() -> None:
    print("Worker started; polling transactional outbox.")
    settings = get_settings()
    while True:
        try:
            with SessionLocal.begin() as session:
                processed = process_next_runner_job(session)
        except SQLAlchemyError as exc:
            print(f"Worker database not ready; retrying: {exc}", flush=True)
            time.sleep(settings.worker_error_retry_seconds)
            continue
        if processed:
            continue
        time.sleep(settings.worker_idle_poll_seconds)


if __name__ == "__main__":
    main()
