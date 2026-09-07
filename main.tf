# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}



# IAM Role for Lambda
resource "aws_iam_role" "lambda_execution" {
  name = "${var.lambda_function_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.lambda_function_name}-role"
    }
  )
}

# IAM Policy for Lambda
resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.lambda_function_name}-policy"
  description = "Policy for IAM Scanner Lambda function"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${var.lambda_function_name}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:Get*",
          "iam:List*",
          "iam:Generate*"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudtrail:LookupEvents"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name = "${var.lambda_function_name}-policy"
    }
  )
}

# Note: IAM policy explicitly depends on S3 bucket being fully created
# to avoid circular dependency issues during resource creation

# Attach Policy to Role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Archive Lambda source code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda_function.zip"
}

# Lambda Function
resource "aws_lambda_function" "iam_scanner" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.lambda_function_name
  role            = aws_iam_role.lambda_execution.arn
  handler         = "iam_scanner.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.11"

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  layers = ["arn:aws:lambda:${var.aws_region}:336392948345:layer:AWSSDKPandas-Python311:35"]

  ephemeral_storage {
    size = var.lambda_ephemeral_storage
  }

  environment {
    variables = {
      S3_BUCKET_NAME = var.s3_bucket_name
      REPORT_PREFIX  = var.s3_report_prefix
    }
  }

  tags = merge(
    var.tags,
    {
      Name = var.lambda_function_name
    }
  )

  depends_on = [aws_iam_role_policy_attachment.lambda_policy_attachment]
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.lambda_function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
