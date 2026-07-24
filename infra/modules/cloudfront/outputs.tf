output "distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "hosted_zone_id" {
  value = aws_cloudfront_distribution.frontend.hosted_zone_id
}

