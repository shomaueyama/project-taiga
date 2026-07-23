import time

from sqlalchemy.exc import SQLAlchemyError

from taiga.infrastructure.database import SessionLocal
from taiga.runner_jobs import process_next_runner_job


def main() -> None:
    print("Worker started; polling transactional outbox.")
    while True:
        try:
            with SessionLocal.begin() as session:
                processed = process_next_runner_job(session)
        except SQLAlchemyError as exc:
            print(f"Worker database not ready; retrying: {exc}", flush=True)
            time.sleep(30)
            continue
        if processed:
            continue
        time.sleep(30)


if __name__ == "__main__":
    main()
