#!/usr/bin/env python3
"""Prepare a Neon database connection for Project Taiga without printing secrets."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import ssl
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


API_BASE_URL = "https://console.neon.tech/api/v2"
DEFAULT_PROJECT_NAME = "project-taiga"
DEFAULT_DATABASE_NAME = "taiga"
DEFAULT_ROLE_NAME = "taiga"
FINISHED_OPERATION_STATUSES = {"finished", "failed", "error", "cancelled"}


class NeonApiError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create or reuse a Neon project and write a gitignored env file with DATABASE_URL."
        )
    )
    parser.add_argument("--project-name", default=os.getenv("NEON_PROJECT_NAME", DEFAULT_PROJECT_NAME))
    parser.add_argument("--project-id", default=os.getenv("NEON_PROJECT_ID"))
    parser.add_argument("--org-id", default=os.getenv("NEON_ORG_ID"))
    parser.add_argument("--region-id", default=os.getenv("NEON_REGION_ID"))
    parser.add_argument("--database-name", default=os.getenv("NEON_DATABASE_NAME", DEFAULT_DATABASE_NAME))
    parser.add_argument("--role-name", default=os.getenv("NEON_ROLE_NAME", DEFAULT_ROLE_NAME))
    parser.add_argument("--env-file", default=os.getenv("NEON_ENV_FILE", ".env.neon.local"))
    parser.add_argument("--pooled", action="store_true", help="Store Neon pooled connection URI.")
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create the project when no matching project exists.",
    )
    parser.add_argument(
        "--migrate-command",
        action="store_true",
        help="Print the redacted Alembic command to run after reviewing the env file.",
    )
    return parser.parse_args()


def request_json(
    method: str,
    path: str,
    api_key: str,
    *,
    query: dict[str, str | bool | int | None] | None = None,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    query_items = {key: value for key, value in (query or {}).items() if value is not None}
    url = f"{API_BASE_URL}{path}"
    if query_items:
        url = f"{url}?{urlencode(query_items)}"

    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30, context=ssl.create_default_context()) as response:
            payload = response.read()
    except HTTPError as exc:
        raise NeonApiError(sanitized_http_error(exc)) from exc
    except URLError as exc:
        raise NeonApiError(f"Neon API network error: {exc.reason}") from exc

    if not payload:
        return {}
    return json.loads(payload)


def sanitized_http_error(exc: HTTPError) -> str:
    try:
        payload = json.loads(exc.read().decode("utf-8", "replace"))
    except (ValueError, OSError):
        return f"Neon API HTTP {exc.code}"

    message = payload.get("message") or payload.get("error") or payload.get("detail")
    if isinstance(message, str):
        return f"Neon API HTTP {exc.code}: {message}"
    return f"Neon API HTTP {exc.code}"


def list_matching_projects(api_key: str, project_name: str, org_id: str | None) -> list[dict[str, Any]]:
    payload = request_json(
        "GET",
        "/projects",
        api_key,
        query={"limit": 100, "search": project_name, "org_id": org_id},
    )
    return [
        project
        for project in payload.get("projects", [])
        if project.get("name") == project_name or project.get("id") == project_name
    ]


def create_project(args: argparse.Namespace, api_key: str) -> dict[str, Any]:
    project: dict[str, Any] = {
        "name": args.project_name,
        "pg_version": 17,
        "branch": {
            "name": "main",
            "database_name": args.database_name,
            "role_name": args.role_name,
        },
    }
    if args.region_id:
        project["region_id"] = args.region_id
    if args.org_id:
        project["org_id"] = args.org_id

    return request_json("POST", "/projects", api_key, body={"project": project})


def wait_for_operations(api_key: str, project_id: str, operations: list[dict[str, Any]]) -> None:
    operation_ids = [operation["id"] for operation in operations if operation.get("id")]
    for operation_id in operation_ids:
        while True:
            payload = request_json("GET", f"/projects/{project_id}/operations/{operation_id}", api_key)
            status = payload.get("operation", {}).get("status")
            if status in FINISHED_OPERATION_STATUSES:
                if status != "finished":
                    raise NeonApiError(f"Neon operation {operation_id} ended with status {status}")
                break
            time.sleep(2)


def get_connection_uri(args: argparse.Namespace, api_key: str, project_id: str) -> str:
    payload = request_json(
        "GET",
        f"/projects/{project_id}/connection_uri",
        api_key,
        query={
            "database_name": args.database_name,
            "role_name": args.role_name,
            "pooled": args.pooled,
        },
    )
    uri = payload.get("connection_uri") or payload.get("uri")
    if not isinstance(uri, str) or not uri:
        raise NeonApiError("Neon API did not return a connection URI")
    return normalize_sqlalchemy_url(uri)


def normalize_sqlalchemy_url(uri: str) -> str:
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql+psycopg://", 1)
    if uri.startswith("postgresql://"):
        return uri.replace("postgresql://", "postgresql+psycopg://", 1)
    return uri


def redact_uri(uri: str) -> str:
    parsed = urlsplit(uri)
    host = parsed.hostname or "<unknown-host>"
    port = f":{parsed.port}" if parsed.port else ""
    db = parsed.path or "/<unknown-db>"
    return urlunsplit((parsed.scheme, f"<redacted>@{host}{port}", db, parsed.query, ""))


def write_env_file(path: Path, database_url: str) -> None:
    content = "\n".join(
        [
            "# Gitignored Neon connection for operator use only.",
            "APP_ENV=production",
            "LOCAL_AUTH_ENABLED=false",
            "RUNNER_ENABLED=false",
            "EXAM_ENABLED=false",
            f"DATABASE_URL={shlex.quote(database_url)}",
            f"MIGRATION_DATABASE_URL={shlex.quote(database_url)}",
            "",
        ]
    )
    path.write_text(content)
    path.chmod(0o600)


def resolve_project(args: argparse.Namespace, api_key: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if args.project_id:
        payload = request_json("GET", f"/projects/{args.project_id}", api_key)
        return payload["project"], []

    matches = list_matching_projects(api_key, args.project_name, args.org_id)
    if len(matches) == 1:
        return matches[0], []
    if len(matches) > 1:
        raise NeonApiError(
            f"More than one Neon project matched {args.project_name!r}; rerun with --project-id."
        )
    if not args.create:
        raise NeonApiError(
            f"No Neon project named {args.project_name!r}; rerun with --create to create it."
        )

    payload = create_project(args, api_key)
    return payload["project"], payload.get("operations", [])


def main() -> int:
    args = parse_args()
    api_key = os.getenv("NEON_API_KEY")
    if not api_key:
        print("NEON_API_KEY is required.", file=sys.stderr)
        return 2

    try:
        project, operations = resolve_project(args, api_key)
        project_id = project["id"]
        if operations:
            wait_for_operations(api_key, project_id, operations)
        database_url = get_connection_uri(args, api_key, project_id)
        write_env_file(Path(args.env_file), database_url)
    except NeonApiError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(f"Neon project: {project.get('name')} ({project.get('region_id', 'unknown region')})")
    print(f"Env file written: {args.env_file}")
    print(f"DATABASE_URL: {redact_uri(database_url)}")
    if args.migrate_command:
        print("Migration command:")
        print(f"cd backend && set -a && source ../{args.env_file} && set +a && ../.venv/bin/alembic upgrade head")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
