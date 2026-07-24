resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnets"
  subnet_ids = var.private_subnet_ids
}

resource "aws_db_instance" "postgres" {
  identifier                          = "${var.name_prefix}-postgres"
  engine                              = "postgres"
  engine_version                      = "17"
  instance_class                      = var.instance_class
  allocated_storage                   = var.allocated_storage
  db_name                             = var.database_name
  username                            = "taiga"
  manage_master_user_password         = true
  db_subnet_group_name                = aws_db_subnet_group.this.name
  vpc_security_group_ids              = [var.security_group_id]
  storage_encrypted                   = true
  backup_retention_period             = 7
  copy_tags_to_snapshot               = true
  deletion_protection                 = var.deletion_protection
  multi_az                            = var.multi_az
  performance_insights_enabled        = true
  iam_database_authentication_enabled = false
  skip_final_snapshot                 = false
  final_snapshot_identifier           = "${var.name_prefix}-postgres-final"
}

