output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.iam_scanner.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.iam_scanner.arn
}

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for audit reports"
  value       = aws_s3_bucket.audit_reports.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.audit_reports.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch Log Group for Lambda logs"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}
