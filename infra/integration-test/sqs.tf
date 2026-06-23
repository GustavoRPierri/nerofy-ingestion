resource "aws_sqs_queue" "events_test" {
  name                       = "nerofy-events-test-${local.suffix}"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
}

resource "aws_sqs_queue_policy" "events_test" {
  queue_url = aws_sqs_queue.events_test.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "apigateway.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events_test.arn
    }]
  })
}
