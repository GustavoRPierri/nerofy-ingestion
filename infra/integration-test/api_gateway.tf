# ── IAM: API Gateway → SQS ────────────────────────────────────────────────────

resource "aws_iam_role" "apigw_sqs_test" {
  name = "nerofy-apigw-sqs-test-role-${local.suffix}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "apigateway.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "apigw_sqs_test" {
  role = aws_iam_role.apigw_sqs_test.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.events_test.arn
    }]
  })
}

# ── REST API ──────────────────────────────────────────────────────────────────

resource "aws_api_gateway_rest_api" "webhook_test" {
  name = "nerofy-webhook-test-${local.suffix}"
}

resource "aws_api_gateway_resource" "webhook_test" {
  rest_api_id = aws_api_gateway_rest_api.webhook_test.id
  parent_id   = aws_api_gateway_rest_api.webhook_test.root_resource_id
  path_part   = "webhook"
}

resource "aws_api_gateway_method" "webhook_post_test" {
  rest_api_id   = aws_api_gateway_rest_api.webhook_test.id
  resource_id   = aws_api_gateway_resource.webhook_test.id
  http_method   = "POST"
  authorization = "NONE"
}

# ── Integração API Gateway → SQS ─────────────────────────────────────────────

resource "aws_api_gateway_integration" "sqs_test" {
  rest_api_id             = aws_api_gateway_rest_api.webhook_test.id
  resource_id             = aws_api_gateway_resource.webhook_test.id
  http_method             = aws_api_gateway_method.webhook_post_test.http_method
  type                    = "AWS"
  integration_http_method = "POST"
  uri                     = "arn:aws:apigateway:${var.aws_region}:sqs:path/${data.aws_caller_identity.current.account_id}/${aws_sqs_queue.events_test.name}"
  credentials             = aws_iam_role.apigw_sqs_test.arn

  request_parameters = {
    "integration.request.header.Content-Type" = "'application/x-www-form-urlencoded'"
  }

  request_templates = {
    "application/json" = "Action=SendMessage&MessageBody=$util.urlEncode($input.body)"
  }
}

resource "aws_api_gateway_integration_response" "sqs_200_test" {
  rest_api_id = aws_api_gateway_rest_api.webhook_test.id
  resource_id = aws_api_gateway_resource.webhook_test.id
  http_method = aws_api_gateway_method.webhook_post_test.http_method
  status_code = "200"

  response_templates = {
    "application/json" = "{\"message\": \"Evento recebido\"}"
  }

  depends_on = [aws_api_gateway_integration.sqs_test]
}

resource "aws_api_gateway_method_response" "webhook_200_test" {
  rest_api_id = aws_api_gateway_rest_api.webhook_test.id
  resource_id = aws_api_gateway_resource.webhook_test.id
  http_method = aws_api_gateway_method.webhook_post_test.http_method
  status_code = "200"
}

# ── Deploy + Stage ────────────────────────────────────────────────────────────

resource "aws_api_gateway_deployment" "webhook_test" {
  rest_api_id = aws_api_gateway_rest_api.webhook_test.id

  depends_on = [
    aws_api_gateway_integration.sqs_test,
    aws_api_gateway_integration_response.sqs_200_test,
  ]
}

resource "aws_api_gateway_stage" "test" {
  rest_api_id   = aws_api_gateway_rest_api.webhook_test.id
  deployment_id = aws_api_gateway_deployment.webhook_test.id
  stage_name    = "test"
}
