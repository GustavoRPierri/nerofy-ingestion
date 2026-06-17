resource "aws_iam_role" "lambda_local" {
  name = "lambda-local-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_lambda_function" "ingestion_local" {
  filename         = "${path.module}/../../lambda_local.zip"
  function_name    = "nerofy-ingestion-local"
  role             = aws_iam_role.lambda_local.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 256
  source_code_hash = filebase64sha256("${path.module}/../../lambda_local.zip")

  environment {
    variables = {
      EXECUCAO             = "local"
      S3_BRONZE_BUCKET     = aws_s3_bucket.bronze.bucket
      DYNAMO_AUTH_TABLE    = aws_dynamodb_table.pluggy_auth.name
      DYNAMO_SYNC_TABLE    = aws_dynamodb_table.transaction_sync.name
      PLUGGY_CLIENT_SECRET = "mock-secret-local"
      LOG_LEVEL            = "DEBUG"
    }
  }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn        = aws_sqs_queue.events.arn
  function_name           = aws_lambda_function.ingestion_local.arn
  batch_size              = 1
  function_response_types = ["ReportBatchItemFailures"]
}
