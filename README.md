# IAM-Lens
Infrastructure as Code for deploying an IAM Scanner Lambda function using Terraform.

## Overview

This project deploys an AWS Lambda function that scans IAM resources and generates audit reports. The reports are stored in an S3 bucket for analysis and compliance purposes.

## Architecture

The Terraform configuration creates the following resources:

- **Lambda Function**: `iam-scanner-lambda`
  - Runtime: Python 3.11
  - Memory: 512 MB
  - Timeout: 5 minutes (300 seconds)
  - Ephemeral storage: 512 MB

- **S3 Bucket**: `my-audit-report-bucket`
  - Versioning enabled
  - Server-side encryption (AES256)
  - Public access blocked
  - Prefix: `iam-audit-reports/`

- **IAM Role and Policy**
  - Lambda execution role
  - Permissions for CloudWatch Logs
  - Permissions for S3 bucket access
  - Read-only IAM permissions for scanning

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS account with permissions to create Lambda, IAM, and S3 resources

## Directory Structure

```
.
├── main.tf              # Main Terraform configuration
├── variables.tf         # Input variables
├── outputs.tf          # Output values
├── versions.tf         # Terraform version constraints
├── lambda/
│   ├── iam_scanner.py  # Lambda function code (dummy implementation)
│   └── requirements.txt # Python dependencies
└── README.md           # This file
```

## Usage

### 1. Initialize Terraform

```bash
terraform init
```

### 2. Review the Plan

```bash
terraform plan
```

### 3. Deploy the Infrastructure

```bash
terraform apply
```

### 4. Invoke the Lambda Function

After deployment, you can test the Lambda function:

```bash
aws lambda invoke --function-name iam-scanner-lambda output.json
cat output.json
```

## Customization

You can customize the deployment by modifying `variables.tf` or creating a `terraform.tfvars` file:

```hcl
aws_region = "us-west-2"
lambda_memory_size = 1024
lambda_timeout = 600
s3_bucket_name = "my-custom-audit-bucket"
```

## Lambda Implementation

The current Lambda function (`lambda/iam_scanner.py`) contains a dummy implementation. To make it functional:

1. Implement IAM scanning logic using boto3
2. Add report generation functionality
3. Implement S3 upload for audit reports
4. Update `requirements.txt` if additional dependencies are needed
5. Consider creating a Lambda Layer for dependencies

## Outputs

After deployment, Terraform will output:

- Lambda function name and ARN
- Lambda execution role ARN
- S3 bucket name and ARN
- CloudWatch Log Group name

## Security Considerations

- The S3 bucket is configured with encryption and public access blocked
- IAM permissions follow the principle of least privilege
- Lambda function has read-only IAM permissions for scanning
- CloudWatch Logs are enabled for monitoring and debugging

## Clean Up

### Manual Cleanup

To destroy all resources created by Terraform:

```bash
terraform destroy
```

## GitHub Actions Workflows

This project includes GitHub Actions workflows for automated deployment and infrastructure management:

### 1. Terraform Deploy (terraform-deploy.yml)

Standard deployment workflow that runs on:
- Push to main branch
- Manual trigger with options to plan/apply/destroy

**Features:**
- Environment selection (dev/prod)
- Terraform action selection (plan/apply/destroy)
- AWS authentication via access keys or OIDC

### 2. Terraform Destroy and Rebuild (terraform-destroy-rebuild.yml)

Specialized workflow for destroying all resources from scratch and rebuilding them.

**Features:**
- Manual trigger only (workflow_dispatch)
- Auto-approves destroy action (no manual confirmation required)
- Auto-approves rebuild/apply action
- Automatically executes destroy → wait → rebuild sequence
- Environment selection (dev/prod)

**Usage:**
1. Go to Actions tab in GitHub
2. Select "Terraform Destroy and Rebuild" workflow
3. Click "Run workflow"
4. Select environment (dev/prod)
5. Confirm execution

**⚠️ Warning:** This workflow will destroy ALL infrastructure resources and rebuild them. Use with caution in production environments.

## Next Steps

1. Implement the actual IAM scanning logic in `lambda/iam_scanner.py`
2. Add EventBridge rule for scheduled execution
3. Configure SNS notifications for scan results
4. Add additional IAM checks and compliance rules
5. Implement report parsing and visualization

## License

This project is provided as-is for educational and deployment purposes.
