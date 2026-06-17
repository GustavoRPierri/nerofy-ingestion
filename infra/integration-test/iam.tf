resource "aws_iam_role" "lambda_exec_test" {
  name = "nerofy-ingestion-test-role-${local.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_test" {
  role       = aws_iam_role.lambda_exec_test.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_custom_test" {
  name = "nerofy-ingestion-test-policy-${local.suffix}"
  role = aws_iam_role.lambda_exec_test.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "S3Bronze"
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.bronze_test.arn}/*"
      },
      {
        Sid    = "DynamoDB"
        Effect = "Allow"
        Action = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"]
        Resource = [
          aws_dynamodb_table.pluggy_auth_test.arn,
          aws_dynamodb_table.transaction_sync_test.arn,
        ]
      },
    ]
  })
}
