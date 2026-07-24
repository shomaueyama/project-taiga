#!/usr/bin/env bash
set -euo pipefail

if [[ "${ALLOW_TAIGA_TERRAFORM_APPLY:-}" != "yes" ]]; then
  echo "Refusing terraform apply. Set ALLOW_TAIGA_TERRAFORM_APPLY=yes after explicit owner approval." >&2
  exit 1
fi

environment="${1:-staging}"
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_dir="${root_dir}/environments/${environment}"

if [[ ! -d "${env_dir}" ]]; then
  echo "Unknown Terraform environment: ${environment}" >&2
  exit 1
fi

cd "${env_dir}"
terraform init
terraform apply

