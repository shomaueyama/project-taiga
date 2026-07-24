output "alb_dns_name" {
  value = module.alb.alb_dns_name
}

output "cloudfront_domain_name" {
  value = module.cloudfront.domain_name
}

output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

output "github_actions_deploy_role_arn" {
  value = module.github_oidc.deploy_role_arn
}

