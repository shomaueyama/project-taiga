variable "name_prefix" {
  type = string
}

variable "force_destroy" {
  type    = bool
  default = false
}

variable "cors_allowed_origins" {
  type    = list(string)
  default = []
}

