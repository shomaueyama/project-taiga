output "alb_security_group_id" {
  value = aws_security_group.alb.id
}

output "backend_security_group_id" {
  value = aws_security_group.backend.id
}

output "worker_security_group_id" {
  value = aws_security_group.worker.id
}

output "rds_security_group_id" {
  value = aws_security_group.rds.id
}

