terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # key é injetado via -backend-config no CI para garantir isolamento por run_id:
  # terraform init -backend-config="key=nerofy-finance-test/<run_id>/terraform.tfstate"
  backend "s3" {
    bucket         = "nerofy-terraform-state"
    region         = "sa-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
