FROM python:3.13-slim

WORKDIR /workspace/runner
COPY runner_controller.py ./

RUN useradd --create-home --uid 10002 runner
USER runner

CMD ["python", "runner_controller.py"]
