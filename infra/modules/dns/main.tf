resource "aws_route53_record" "frontend" {
  count   = var.zone_id == null || var.frontend_domain_name == null ? 0 : 1
  zone_id = var.zone_id
  name    = var.frontend_domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api" {
  count   = var.zone_id == null || var.api_domain_name == null ? 0 : 1
  zone_id = var.zone_id
  name    = var.api_domain_name
  type    = "A"

  alias {
    name                   = var.alb_dns_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

