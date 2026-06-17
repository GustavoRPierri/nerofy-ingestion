resource "aws_s3_bucket" "bronze_test" {
  # run_id garante unicidade global entre execuções de CI
  bucket        = "nerofy-bronze-test-${var.run_id}"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "bronze_test" {
  bucket = aws_s3_bucket.bronze_test.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bronze_test" {
  bucket = aws_s3_bucket.bronze_test.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "bronze_test" {
  bucket                  = aws_s3_bucket.bronze_test.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
