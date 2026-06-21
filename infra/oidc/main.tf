variable "aws_region" {
  default = "sa-east-1"
}

variable "github_repo" {
  description = "Repositório GitHub no formato owner/repo"
  default     = "GustavoRPierri/nerofy-ingestion"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

# ── Role: deploy em produção (main) ──────────────────────────────────────────

resource "aws_iam_role" "github_deploy" {
  name = "github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_repo}:ref:refs/heads/main",
            "repo:${var.github_repo}:ref:refs/heads/release/*"
          ]
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_deploy" {
  name = "github-actions-deploy-policy"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformState"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::nerofy-terraform-state",
          "arn:aws:s3:::nerofy-terraform-state/*"
        ]
      },
      {
        Sid      = "TerraformLock"
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"]
        Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/terraform-state-lock"
      },
      {
        Sid    = "Lambda"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction", "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration", "lambda:GetFunction",
          "lambda:DeleteFunction", "lambda:AddPermission", "lambda:RemovePermission",
          "lambda:CreateEventSourceMapping", "lambda:UpdateEventSourceMapping",
          "lambda:DeleteEventSourceMapping", "lambda:GetEventSourceMapping",
          "lambda:PublishLayerVersion", "lambda:DeleteLayerVersion",
          "lambda:GetLayerVersion", "lambda:ListLayerVersions",
          "lambda:TagResource", "lambda:UntagResource", "lambda:ListTags"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAM"
        Effect = "Allow"
        Action = [
          "iam:CreateRole", "iam:UpdateRole", "iam:DeleteRole",
          "iam:GetRole", "iam:PassRole",
          "iam:AttachRolePolicy", "iam:DetachRolePolicy",
          "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy",
          "iam:ListAttachedRolePolicies", "iam:ListRolePolicies",
          "iam:TagRole", "iam:UntagRole"
        ]
        Resource = "arn:aws:iam::*:role/nerofy-*"
      },
      {
        Sid    = "S3Bronze"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket", "s3:DeleteBucket",
          "s3:Get*", "s3:PutBucket*", "s3:PutObject",
          "s3:DeleteObject", "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::nerofy-bronze-*",
          "arn:aws:s3:::nerofy-bronze-*/*"
        ]
      },
      {
        Sid    = "DynamoDB"
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable", "dynamodb:DeleteTable",
          "dynamodb:Describe*", "dynamodb:ListTagsOfResource",
          "dynamodb:UpdateTable", "dynamodb:TagResource", "dynamodb:UntagResource",
          "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/Pluggy*"
      },
      {
        Sid    = "SQS"
        Effect = "Allow"
        Action = [
          "sqs:CreateQueue", "sqs:DeleteQueue", "sqs:GetQueueAttributes",
          "sqs:SetQueueAttributes", "sqs:TagQueue", "sqs:GetQueueUrl"
        ]
        Resource = "arn:aws:sqs:${var.aws_region}:*:nerofy-*"
      },
      {
        Sid      = "SSM"
        Effect   = "Allow"
        Action   = ["ssm:GetParameter"]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/nerofy/*"
      },
      {
        Sid    = "APIGateway"
        Effect = "Allow"
        Action = ["apigateway:*"]
        Resource = "arn:aws:apigateway:${var.aws_region}::/restapis*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup", "logs:DeleteLogGroup",
          "logs:DescribeLogGroups", "logs:TagResource"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/nerofy-*"
      }
    ]
  })
}

# ── Role: testes de integração (release/* e hotfix/*) ────────────────────────

resource "aws_iam_role" "github_ci" {
  name = "github-actions-ci"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_repo}:ref:refs/heads/release/*",
            "repo:${var.github_repo}:ref:refs/heads/hotfix/*"
          ]
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_ci" {
  name = "github-actions-ci-policy"
  role = aws_iam_role.github_ci.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformState"
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::nerofy-terraform-state",
          "arn:aws:s3:::nerofy-terraform-state/*"
        ]
      },
      {
        Sid      = "TerraformLock"
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:DeleteItem"]
        Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/terraform-state-lock"
      },
      {
        Sid    = "Lambda"
        Effect = "Allow"
        Action = [
          "lambda:CreateFunction", "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration", "lambda:GetFunction",
          "lambda:DeleteFunction", "lambda:PublishLayerVersion",
          "lambda:DeleteLayerVersion", "lambda:GetLayerVersion",
          "lambda:CreateEventSourceMapping", "lambda:UpdateEventSourceMapping",
          "lambda:DeleteEventSourceMapping", "lambda:GetEventSourceMapping",
          "lambda:InvokeFunction", "lambda:TagResource", "lambda:ListTags"
        ]
        Resource = "*"
      },
      {
        Sid    = "IAM"
        Effect = "Allow"
        Action = [
          "iam:CreateRole", "iam:UpdateRole", "iam:DeleteRole",
          "iam:GetRole", "iam:PassRole",
          "iam:AttachRolePolicy", "iam:DetachRolePolicy",
          "iam:PutRolePolicy", "iam:GetRolePolicy", "iam:DeleteRolePolicy",
          "iam:ListAttachedRolePolicies", "iam:ListRolePolicies",
          "iam:TagRole", "iam:UntagRole"
        ]
        Resource = "arn:aws:iam::*:role/nerofy-*"
      },
      {
        Sid    = "S3Test"
        Effect = "Allow"
        Action = [
          "s3:CreateBucket", "s3:DeleteBucket",
          "s3:Get*", "s3:PutBucket*", "s3:PutObject",
          "s3:DeleteObject", "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::nerofy-bronze-test-*",
          "arn:aws:s3:::nerofy-bronze-test-*/*"
        ]
      },
      {
        Sid    = "DynamoDBTest"
        Effect = "Allow"
        Action = [
          "dynamodb:CreateTable", "dynamodb:DeleteTable",
          "dynamodb:Describe*", "dynamodb:ListTagsOfResource",
          "dynamodb:UpdateTable", "dynamodb:TagResource",
          "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"
        ]
        Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/*-test-*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup", "logs:DeleteLogGroup",
          "logs:DescribeLogGroups", "logs:TagResource"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/nerofy-*"
      }
    ]
  })
}

output "github_deploy_role_arn" {
  description = "ARN da role OIDC para deploy — usar como AWS_ROLE_ARN_DEPLOY no GitHub"
  value       = aws_iam_role.github_deploy.arn
}

output "github_ci_role_arn" {
  description = "ARN da role OIDC para CI — usar como AWS_ROLE_ARN_CI no GitHub"
  value       = aws_iam_role.github_ci.arn
}
