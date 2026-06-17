# IAM role para API Gateway escrever no SQS
resource "aws_iam_role" "apigw_sqs" {
  name = "apigw-sqs-local-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "apigateway.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "apigw_sqs" {
  role = aws_iam_role.apigw_sqs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.events.arn
    }]
  })
}

# REST API
resource "aws_api_gateway_rest_api" "webhook" {
  name = "nerofy-webhook-local"
}

# Recurso /webhook
resource "aws_api_gateway_resource" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  parent_id   = aws_api_gateway_rest_api.webhook.root_resource_id
  path_part   = "webhook"
}

# POST /webhook
resource "aws_api_gateway_method" "webhook_post" {
  rest_api_id   = aws_api_gateway_rest_api.webhook.id
  resource_id   = aws_api_gateway_resource.webhook.id
  http_method   = "POST"
  authorization = "NONE"
}

# Integração API Gateway → SQS
resource "aws_api_gateway_integration" "sqs" {
  rest_api_id             = aws_api_gateway_rest_api.webhook.id
  resource_id             = aws_api_gateway_resource.webhook.id
  http_method             = aws_api_gateway_method.webhook_post.http_method
  type                    = "AWS"
  integration_http_method = "POST"
  uri                     = "arn:aws:apigateway:sa-east-1:sqs:path/000000000000/${aws_sqs_queue.events.name}"
  credentials             = aws_iam_role.apigw_sqs.arn

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/x-www-form-urlencoded'"
  }

  # Envia o body do POST como MessageBody no SQS
  request_templates = {
    "application/json" = "Action=SendMessage&MessageBody=$util.urlEncode($input.body)"
  }
}

# Resposta da integração (200 OK)
resource "aws_api_gateway_integration_response" "sqs_200" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  resource_id = aws_api_gateway_resource.webhook.id
  http_method = aws_api_gateway_method.webhook_post.http_method
  status_code = "200"

  response_templates = {
    "application/json" = "{\"message\": \"Evento recebido\"}"
  }

  depends_on = [aws_api_gateway_integration.sqs]
}

resource "aws_api_gateway_method_response" "webhook_200" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id
  resource_id = aws_api_gateway_resource.webhook.id
  http_method = aws_api_gateway_method.webhook_post.http_method
  status_code = "200"
}

# Deploy + stage
resource "aws_api_gateway_deployment" "webhook" {
  rest_api_id = aws_api_gateway_rest_api.webhook.id

  depends_on = [
    aws_api_gateway_integration.sqs,
    aws_api_gateway_integration_response.sqs_200,
  ]
}

resource "aws_api_gateway_stage" "local" {
  rest_api_id   = aws_api_gateway_rest_api.webhook.id
  deployment_id = aws_api_gateway_deployment.webhook.id
  stage_name    = "local"
}

output "webhook_url" {
  value       = "http://localhost:4566/restapis/${aws_api_gateway_rest_api.webhook.id}/local/_user_request_/webhook"
  description = "URL do endpoint para usar no Postman"
}
