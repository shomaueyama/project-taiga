#!/usr/bin/env bash
set -euo pipefail

environment="${1:-staging}"
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_dir="${root_dir}/environments/${environment}"

if [[ ! -d "${env_dir}" ]]; then
  echo "Unknown Terraform environment: ${environment}" >&2
  exit 1
fi

cd "${env_dir}"
terraform init -backend=false
terraform fmt -check -recursive ../..
terraform validate
terraform plan -refresh=false

