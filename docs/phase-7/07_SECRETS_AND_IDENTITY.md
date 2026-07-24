# Secrets And Identity

Secrets must not be committed to the repository.

The Terraform foundation models GitHub Actions OIDC roles and stores application database
configuration in SSM SecureString. Production deployment must replace placeholders through
CI environment variables or an approved secret management workflow.

The GitHub OIDC provider resource may already exist in an AWS account. If so, import it
into Terraform state rather than creating a duplicate provider.

