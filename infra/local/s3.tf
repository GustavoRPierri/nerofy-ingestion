resource "aws_s3_bucket" "bronze" {
  bucket        = "nerofy-bronze-dev"
  force_destroy = true
}
