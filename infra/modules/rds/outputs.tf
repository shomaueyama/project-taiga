output "endpoint" {
  value = aws_db_instance.postgres.endpoint
}

output "identifier" {
  value = aws_db_instance.postgres.identifier
}

output "address" {
  value = aws_db_instance.postgres.address
}

output "secret_arn" {
  value = aws_db_instance.postgres.master_user_secret[0].secret_arn
}
