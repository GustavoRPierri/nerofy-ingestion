locals {
  # Últimos 10 chars do run_id para nomes curtos e únicos
  suffix = substr(var.run_id, length(var.run_id) > 10 ? length(var.run_id) - 10 : 0, -1)
}

data "aws_caller_identity" "current" {}

# ── Lambda Layer ──────────────────────────────────────────────────────────────

resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${path.module}/../../lambda_layer.zip"
  layer_name          = "nerofy-ingestion-test-deps-${local.suffix}"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${path.module}/../../lambda_layer.zip")
}

# ── Lambda Function ───────────────────────────────────────────────────────────

resource "aws_lambda_function" "ingestion_test" {
  filename         = "${path.module}/../../lambda_function.zip"
  function_name    = "nerofy-ingestion-test-${local.suffix}"
  role             = aws_iam_role.lambda_exec_test.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../../lambda_function.zip")
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      S3_BRONZE_BUCKET       = aws_s3_bucket.bronze_test.bucket
      DYNAMO_AUTH_TABLE      = aws_dynamodb_table.pluggy_auth_test.name
      DYNAMO_SYNC_TABLE      = aws_dynamodb_table.transaction_sync_test.name
      PLUGGY_API_URL         = "https://api.pluggy.ai"
      PLUGGY_CLIENT_SECRET   = "test-integration-placeholder"
      SSM_PLUGGY_SECRET_PATH = var.ssm_pluggy_secret_path
      LOG_LEVEL              = var.log_level
      ENV                    = "test"
      # EXECUCAO=local faz com que settings.py não tente buscar o secret no SSM
      EXECUCAO               = "local"
    }
  }
}
