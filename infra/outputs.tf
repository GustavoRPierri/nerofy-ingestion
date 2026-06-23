output "lambda_function_name" {
  value = aws_lambda_function.ingestion.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.ingestion.arn
}

output "lambda_layer_arn" {
  value = aws_lambda_layer_version.dependencies.arn
}

output "s3_bronze_bucket" {
  value = aws_s3_bucket.bronze.bucket
}

output "sqs_queue_url" {
  value = aws_sqs_queue.events.url
}

output "sqs_queue_arn" {
  value = aws_sqs_queue.events.arn
}

output "dynamo_auth_table" {
  value = aws_dynamodb_table.pluggy_auth.name
}

output "dynamo_sync_table" {
  value = aws_dynamodb_table.transaction_sync.name
}

output "webhook_url" {
  description = "URL do endpoint para configurar na Pluggy como webhook"
  value       = "https://${aws_api_gateway_rest_api.webhook.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.prod.stage_name}/webhook"
}

