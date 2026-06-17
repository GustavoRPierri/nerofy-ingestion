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
