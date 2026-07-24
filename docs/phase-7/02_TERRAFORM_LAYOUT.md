# Terraform Layout

Terraform files are under `infra/`.

- `modules/`: reusable AWS modules.
- `environments/staging`: staging root module.
- `environments/production`: production root module.
- `scripts/`: operator entry points.

Validation is designed to run with:

```bash
terraform init -backend=false
terraform validate
```

This avoids creating or reading remote state during pull request validation.

