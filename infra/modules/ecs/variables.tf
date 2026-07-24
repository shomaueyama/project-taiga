variable "name_prefix" {
  type = string
}

variable "aws_region" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "backend_security_group_id" {
  type = string
}

variable "worker_security_group_id" {
  type = string
}

variable "backend_target_group_arn" {
  type = string
}

variable "backend_image" {
  type = string
}

variable "worker_image" {
  type = string
}

variable "database_url_parameter_arn" {
  type = string
}

variable "uploads_bucket_id" {
  type = string
}

variable "backend_desired_count" {
  type    = number
  default = 1
}

variable "worker_desired_count" {
  type    = number
  default = 1
}

variable "app_port" {
  type    = number
  default = 8000
}

