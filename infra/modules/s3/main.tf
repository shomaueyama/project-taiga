resource "aws_s3_bucket" "frontend" {
  bucket        = "${var.name_prefix}-frontend"
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket" "uploads" {
  bucket        = "${var.name_prefix}-uploads"
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket_public_access_block" "all" {
  for_each = {
    frontend = aws_s3_bucket.frontend.id
    uploads  = aws_s3_bucket.uploads.id
  }

  bucket                  = each.value
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "all" {
  for_each = {
    frontend = aws_s3_bucket.frontend.id
    uploads  = aws_s3_bucket.uploads.id
  }

  bucket = each.value

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "uploads" {
  bucket = aws_s3_bucket.uploads.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_configuration" "uploads" {
  count  = length(var.cors_allowed_origins) > 0 ? 1 : 0
  bucket = aws_s3_bucket.uploads.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = var.cors_allowed_origins
    expose_headers  = ["ETag"]
    max_age_seconds = 300
  }
}

