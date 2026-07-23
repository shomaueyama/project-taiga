FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY alembic.ini ./
COPY src ./src
COPY tests ./tests
COPY alembic ./alembic

EXPOSE 8000
CMD ["uvicorn", "taiga.main:app", "--host", "0.0.0.0", "--port", "8000"]
