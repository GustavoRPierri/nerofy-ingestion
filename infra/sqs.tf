resource "aws_sqs_queue" "events" {
  name                       = "nerofy-events"
  visibility_timeout_seconds = 300  # >= Lambda timeout
  message_retention_seconds  = 86400
}

# Permite que a Pluggy (API Gateway) envie mensagens para a fila
resource "aws_sqs_queue_policy" "events" {
  queue_url = aws_sqs_queue.events.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "apigateway.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.events.arn
    }]
  })
}
