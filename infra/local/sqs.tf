resource "aws_sqs_queue" "events" {
  name                       = "nerofy-events"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 86400
}