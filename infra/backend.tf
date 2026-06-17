terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Estado remoto no S3 — crie o bucket e a tabela antes do primeiro deploy.
  # Bucket:  nerofy-terraform-state  (versioning habilitado)
  # DynamoDB: terraform-state-lock   (PK=LockID, tipo String)
  backend "s3" {
    bucket         = "nerofy-terraform-state"
    key            = "nerofy-finance/terraform.tfstate"
    region         = "sa-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
    profile        = "nerofy"
  }
}

provider "aws" {
  region = var.aws_region
}
