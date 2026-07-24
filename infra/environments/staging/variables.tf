variable "aws_region" {
  type    = string
  default = "ap-northeast-1"
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "name_prefix" {
  type    = string
  default = "taiga-staging"
}

variable "availability_zones" {
  type    = list(string)
  default = ["ap-northeast-1a", "ap-northeast-1c"]
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.42.0.0/24", "10.42.1.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.42.10.0/24", "10.42.11.0/24"]
}

variable "enable_nat_gateway" {
  type    = bool
  default = false
}

variable "certificate_arn" {
  type    = string
  default = null
}

variable "cloudfront_certificate_arn" {
  type    = string
  default = null
}

variable "route53_zone_id" {
  type    = string
  default = null
}

variable "frontend_domain_name" {
  type    = string
  default = null
}

variable "api_domain_name" {
  type    = string
  default = null
}

variable "backend_image" {
  type    = string
  default = "REPLACE_ME_BACKEND_IMAGE"
}

variable "worker_image" {
  type    = string
  default = "REPLACE_ME_WORKER_IMAGE"
}

variable "database_url_parameter_value" {
  type      = string
  sensitive = true
  default   = "REPLACE_AT_DEPLOY_TIME"
}

variable "github_repository" {
  type    = string
  default = "shomaueyama/project-taiga"
}

variable "github_oidc_provider_arn" {
  type    = string
  default = "arn:aws:iam::000000000000:oidc-provider/token.actions.githubusercontent.com"
}
