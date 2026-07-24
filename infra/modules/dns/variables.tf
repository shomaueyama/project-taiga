variable "zone_id" {
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

variable "cloudfront_domain_name" {
  type = string
}

variable "cloudfront_zone_id" {
  type = string
}

variable "alb_dns_name" {
  type = string
}

variable "alb_zone_id" {
  type = string
}

