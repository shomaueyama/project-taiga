from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass


SCENARIOS = {
    "smoke": {"requests": 40, "concurrency": 2},
    "baseline": {"requests": 200, "concurrency": 8},
    "stress": {"requests": 500, "concurrency": 20},
}
READ_PATHS = (
    "/health",
    "/api/v1/dashboard",
    "/api/v1/assignments",
    "/api/v1/progress",
    "/api/v1/reviews/queue",
)
PATH_USERS = {
    "/api/v1/reviews/queue": "reviewer@example.local",
}


@dataclass(frozen=True)
class Sample:
    path: str
    status: int
    elapsed_ms: float
    bytes_read: int


def request_once(base_url: str, path: str) -> Sample:
    headers = {}
    if path.startswith("/api/"):
        email = PATH_USERS.get(path, "taiga@example.local")
        headers["Authorization"] = f"Bearer local:{email}"
    start = time.perf_counter()
    request = urllib.request.Request(f"{base_url}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        body = exc.read()
        status = exc.code
    return Sample(
        path=path,
        status=status,
        elapsed_ms=(time.perf_counter() - start) * 1000,
        bytes_read=len(body),
    )


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(round((percentile_value / 100) * (len(ordered) - 1))))
    return ordered[index]


def run(base_url: str, requests: int, concurrency: int) -> dict[str, object]:
    start = time.perf_counter()
    samples: list[Sample] = []
    errors = 0
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(request_once, base_url, READ_PATHS[index % len(READ_PATHS)])
            for index in range(requests)
        ]
        for future in as_completed(futures):
            sample = future.result()
            samples.append(sample)
            if sample.status >= 500:
                errors += 1
    elapsed = time.perf_counter() - start
    latencies = [sample.elapsed_ms for sample in samples]
    return {
        "baseUrl": base_url,
        "requests": requests,
        "concurrency": concurrency,
        "durationSeconds": round(elapsed, 3),
        "throughputRps": round(len(samples) / elapsed, 2),
        "p50Ms": round(statistics.median(latencies), 2),
        "p95Ms": round(percentile(latencies, 95), 2),
        "p99Ms": round(percentile(latencies, 99), 2),
        "errorRate": round(errors / len(samples), 4),
        "bytesRead": sum(sample.bytes_read for sample in samples),
        "statusCounts": {
            str(status): sum(1 for sample in samples if sample.status == status)
            for status in sorted({sample.status for sample in samples})
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a local Project Taiga read-path load test.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="baseline")
    parser.add_argument("--requests", type=int)
    parser.add_argument("--concurrency", type=int)
    args = parser.parse_args()
    scenario = SCENARIOS[args.scenario]
    requests = args.requests or scenario["requests"]
    concurrency = args.concurrency or scenario["concurrency"]
    print(json.dumps(run(args.base_url.rstrip("/"), requests, concurrency), sort_keys=True))


if __name__ == "__main__":
    main()
