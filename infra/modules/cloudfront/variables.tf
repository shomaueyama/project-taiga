variable "name_prefix" {
  type = string
}

variable "frontend_bucket_id" {
  type = string
}

variable "frontend_bucket_regional_domain_name" {
  type = string
}

variable "aliases" {
  type    = list(string)
  default = []
}

variable "certificate_arn" {
  type    = string
  default = null
}

