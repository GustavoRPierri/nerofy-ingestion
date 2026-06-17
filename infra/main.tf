# ── Lambda Layer (dependências do requirements.txt) ──────────────────────────

resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${path.module}/../lambda_layer.zip"
  layer_name          = "${var.lambda_function_name}-deps"
  compatible_runtimes = ["python3.12"]
  source_code_hash    = filebase64sha256("${path.module}/../lambda_layer.zip")
  description         = "Dependencias Python do requirements.txt"
}

# ── Lambda Function ───────────────────────────────────────────────────────────

resource "aws_lambda_function" "ingestion" {
  filename         = "${path.module}/../lambda_function.zip"
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_exec.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../lambda_function.zip")
  layers           = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = {
      S3_BRONZE_BUCKET       = aws_s3_bucket.bronze.bucket
      DYNAMO_AUTH_TABLE      = aws_dynamodb_table.pluggy_auth.name
      DYNAMO_SYNC_TABLE      = aws_dynamodb_table.transaction_sync.name
      PLUGGY_API_URL         = "https://api.pluggy.ai"
      SSM_PLUGGY_SECRET_PATH = var.ssm_pluggy_secret_path
      LOG_LEVEL              = var.log_level
      ENV                    = var.environment
      EXECUCAO               = "aws"
    }
  }
}

# ── SQS → Lambda trigger ──────────────────────────────────────────────────────

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn        = aws_sqs_queue.events.arn
  function_name           = aws_lambda_function.ingestion.arn
  batch_size              = 10
  function_response_types = ["ReportBatchItemFailures"]
}
