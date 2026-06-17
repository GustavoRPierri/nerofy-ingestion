variable "aws_region" {
  description = "Região AWS"
  default     = "sa-east-1"
}

variable "run_id" {
  description = "GitHub Actions run ID — garante unicidade dos recursos por execução de CI"
  type        = string
}

variable "ssm_pluggy_secret_path" {
  description = "Caminho SSM (não usado em testes, apenas para evitar erro de validação)"
  default     = "/nerofy/pluggy/client_secret"
}

variable "log_level" {
  description = "Nível de log da Lambda de teste"
  default     = "DEBUG"
}
