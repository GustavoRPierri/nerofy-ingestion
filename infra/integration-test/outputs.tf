output "lambda_function_name" {
  value = aws_lambda_function.ingestion_test.function_name
}

output "s3_bucket_name" {
  value = aws_s3_bucket.bronze_test.bucket
}

output "dynamo_auth_table" {
  value = aws_dynamodb_table.pluggy_auth_test.name
}

output "dynamo_sync_table" {
  value = aws_dynamodb_table.transaction_sync_test.name
}

output "sqs_queue_url" {
  value = aws_sqs_queue.events_test.url
}

output "sqs_queue_arn" {
  value = aws_sqs_queue.events_test.arn
}

output "webhook_url" {
  value = "https://${aws_api_gateway_rest_api.webhook_test.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_stage.test.stage_name}/webhook"
}
