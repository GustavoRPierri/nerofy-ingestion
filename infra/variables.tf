variable "aws_region" {
  description = "Região AWS"
  default     = "sa-east-1"
}

variable "lambda_function_name" {
  description = "Nome da função Lambda"
  default     = "nerofy-ingestion"
}

variable "s3_bronze_bucket" {
  description = "Nome do bucket S3 da camada bronze"
  default     = "nerofy-bronze-dev"
}

variable "ssm_pluggy_secret_path" {
  description = "Caminho do parâmetro SSM com o client_secret da Pluggy"
  default     = "/nerofy/pluggy/client_secret"
}

variable "log_level" {
  description = "Nível de log da Lambda"
  default     = "INFO"
}

variable "environment" {
  description = "Ambiente de deploy (dev, prod)"
  default     = "dev"
}
