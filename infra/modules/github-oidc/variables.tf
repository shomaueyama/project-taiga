variable "name_prefix" {
  type = string
}

variable "github_repository" {
  type = string
}

variable "environment_name" {
  type = string
}

variable "create_oidc_provider" {
  type    = bool
  default = false
}

variable "oidc_provider_arn" {
  type    = string
  default = "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com"
}
