import time

from taiga.infrastructure.database import SessionLocal
from taiga.runner_jobs import process_next_runner_job


def main() -> None:
    print("Worker started; polling transactional outbox.")
    while True:
        with SessionLocal.begin() as session:
            processed = process_next_runner_job(session)
        if processed:
            continue
        time.sleep(30)


if __name__ == "__main__":
    main()
