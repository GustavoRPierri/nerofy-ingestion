terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "nerofy-terraform-state"
    key            = "nerofy-finance/oidc/terraform.tfstate"
    region         = "sa-east-1"
    use_lockfile   = true
  }
}

provider "aws" {
  region = "sa-east-1"
}
