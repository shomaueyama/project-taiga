import os
import time


def main() -> None:
    enabled = os.getenv("RUNNER_ENABLED", "false").lower() == "true"
    print(f"Runner controller placeholder started; enabled={enabled}")
    while True:
        time.sleep(30)


if __name__ == "__main__":
    main()
