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
