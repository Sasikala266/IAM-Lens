variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "eu-west-1"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "iam-scanner-lambda"
}

variable "lambda_memory_size" {
  description = "Memory allocation for Lambda function in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function in seconds"
  type        = number
  default     = 300
}

variable "lambda_ephemeral_storage" {
  description = "Ephemeral storage for Lambda function in MB"
  type        = number
  default     = 512
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for audit reports"
  type        = string
  default     = "sasi-audit-report-bucket"
}

variable "s3_report_prefix" {
  description = "Prefix for IAM audit reports in S3"
  type        = string
  default     = "iam-audit-reports"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default     = {
    Project     = "IAM-Lens"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}
