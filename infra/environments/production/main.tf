module "network" {
  source               = "../../modules/network"
  name_prefix          = var.name_prefix
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  enable_nat_gateway   = var.enable_nat_gateway
}

module "security" {
  source      = "../../modules/security"
  name_prefix = var.name_prefix
  vpc_id      = module.network.vpc_id
}

module "ecr" {
  source       = "../../modules/ecr"
  name_prefix  = var.name_prefix
  repositories = ["backend", "frontend", "worker"]
}

module "s3" {
  source               = "../../modules/s3"
  name_prefix          = var.name_prefix
  force_destroy        = false
  cors_allowed_origins = var.frontend_domain_name == null ? [] : ["https://${var.frontend_domain_name}"]
}

resource "aws_ssm_parameter" "database_url" {
  name  = "/taiga/${var.environment}/database-url"
  type  = "SecureString"
  value = var.database_url_parameter_value
}

module "alb" {
  source            = "../../modules/alb"
  name_prefix       = var.name_prefix
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
  security_group_id = module.security.alb_security_group_id
  certificate_arn   = var.certificate_arn
}

module "rds" {
  source              = "../../modules/rds"
  name_prefix         = var.name_prefix
  private_subnet_ids  = module.network.private_subnet_ids
  security_group_id   = module.security.rds_security_group_id
  instance_class      = "db.t4g.small"
  allocated_storage   = 50
  multi_az            = true
  deletion_protection = true
}

module "ecs" {
  source                     = "../../modules/ecs"
  name_prefix                = var.name_prefix
  aws_region                 = var.aws_region
  private_subnet_ids         = module.network.private_subnet_ids
  backend_security_group_id  = module.security.backend_security_group_id
  worker_security_group_id   = module.security.worker_security_group_id
  backend_target_group_arn   = module.alb.backend_target_group_arn
  backend_image              = var.backend_image
  worker_image               = var.worker_image
  database_url_parameter_arn = aws_ssm_parameter.database_url.arn
  uploads_bucket_id          = module.s3.uploads_bucket_id
  backend_desired_count      = 2
  worker_desired_count       = 1
}

module "cloudfront" {
  source                               = "../../modules/cloudfront"
  name_prefix                          = var.name_prefix
  frontend_bucket_id                   = module.s3.frontend_bucket_id
  frontend_bucket_regional_domain_name = module.s3.frontend_bucket_regional_domain_name
  aliases                              = var.frontend_domain_name == null ? [] : [var.frontend_domain_name]
  certificate_arn                      = var.cloudfront_certificate_arn
}

module "dns" {
  source                 = "../../modules/dns"
  zone_id                = var.route53_zone_id
  frontend_domain_name   = var.frontend_domain_name
  api_domain_name        = var.api_domain_name
  cloudfront_domain_name = module.cloudfront.domain_name
  cloudfront_zone_id     = module.cloudfront.hosted_zone_id
  alb_dns_name           = module.alb.alb_dns_name
  alb_zone_id            = module.alb.alb_zone_id
}

module "observability" {
  source         = "../../modules/observability"
  name_prefix    = var.name_prefix
  alb_arn_suffix = module.alb.alb_arn_suffix
  rds_identifier = module.rds.identifier
}

module "github_oidc" {
  source            = "../../modules/github-oidc"
  name_prefix       = var.name_prefix
  github_repository = var.github_repository
  environment_name  = var.environment
  oidc_provider_arn = var.github_oidc_provider_arn
}
