#!/usr/bin/env bash
set -euo pipefail

base_url="${1:?Usage: smoke-test.sh https://api.example.com}"

curl --fail --silent --show-error "${base_url%/}/health" >/dev/null
echo "Health check passed: ${base_url%/}/health"

