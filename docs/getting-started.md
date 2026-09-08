<div align="center">

# 🚀 Getting Started Guide

### Deploy and Run Your First IAM Audit

[← Back to Main](../README.md) | [Features →](features.md) | [Architecture →](architecture.md)

</div>

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Deployment](#-deployment)
3. [Basic Usage](#-basic-usage)
4. [Verification](#-verification)
5. [Next Steps](#-next-steps)

---

## ✅ Prerequisites

Before deploying the IAM Audit Utility, ensure you have the following:

### Required Tools

#### 1️⃣ **Terraform** (>= 1.0)
Infrastructure-as-code tool for deploying AWS resources.

**Installation:**
- **macOS**: `brew install terraform`
- **Linux**: Download from https://developer.hashicorp.com/terraform/downloads
- **Windows**: Download and add to PATH

**Verify installation:**
```bash
terraform --version
# Should show: Terraform v1.0.0 or higher
```

#### 2️⃣ **AWS CLI** (>= 2.0)
Command-line tool for interacting with AWS services.

**Installation:**
- **macOS**: `brew install awscli`
- **Linux/Windows**: Follow instructions at https://aws.amazon.com/cli/

**Verify installation:**
```bash
aws --version
# Should show: aws-cli/2.x.x or higher
```

#### 3️⃣ **AWS Account**
An active AWS account with programmatic access.

### Required AWS Permissions

Your AWS credentials must have permissions to create and manage:

**IAM Resources:**
- `iam:CreateRole`
- `iam:CreatePolicy`
- `iam:AttachRolePolicy`
- `iam:PutRolePolicy`

**Lambda Resources:**
- `lambda:CreateFunction`
- `lambda:UpdateFunctionCode`
- `lambda:UpdateFunctionConfiguration`

**S3 Resources:**
- `s3:CreateBucket`
- `s3:PutBucketPolicy`
- `s3:PutBucketVersioning`
- `s3:PutEncryptionConfiguration`

**CloudWatch Resources:**
- `logs:CreateLogGroup`
- `logs:PutRetentionPolicy`

> 💡 **Tip**: Use `AdministratorAccess` or `PowerUserAccess` policies for initial deployment.

### AWS Configuration

Configure your AWS credentials using one of these methods:

#### Option 1: AWS CLI Configuration (Recommended)
```bash
aws configure
```

You'll be prompted to enter:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

#### Option 2: Environment Variables
```bash
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Option 3: AWS SSO (Single Sign-On)
```bash
aws sso login --profile my-profile
export AWS_PROFILE=my-profile
```

**Verify AWS configuration:**
```bash
aws sts get-caller-identity
```

Should return your AWS account ID and user ARN.

---

## 🏗️ Deployment

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd iam-audit-utility
```

### Step 2: Review Configuration (Optional)

The utility uses sensible defaults, but you can customize by creating a `terraform.tfvars` file:

```hcl
# terraform.tfvars
aws_region          = "us-east-1"
lambda_function_name = "iam-scanner-lambda"
lambda_memory_size   = 512          # MB
lambda_timeout       = 300          # seconds (5 minutes)
s3_bucket_prefix     = "audit-reports"

tags = {
  Environment = "Production"
  Project     = "IAM Audit"
  ManagedBy   = "Terraform"
  Owner       = "<your-team>"
}
```

### Step 3: Initialize Terraform

Download required providers and modules:

```bash
terraform init
```

**Expected output:**
```
Initializing the backend...
Initializing provider plugins...
- Finding latest version of hashicorp/aws...
- Installing hashicorp/aws...

Terraform has been successfully initialized!
```

### Step 4: Review Deployment Plan

Preview what resources will be created:

```bash
terraform plan
```

**Resources to be created:**
- ✅ AWS Lambda function (Python 3.11, 512MB)
- ✅ S3 bucket (encrypted, versioned)
- ✅ IAM execution role for Lambda
- ✅ IAM policies (read-only IAM access, S3 write access)
- ✅ CloudWatch log group

### Step 5: Deploy Infrastructure

Apply the Terraform configuration:

```bash
terraform apply
```

Type `yes` when prompted to confirm deployment.

**Deployment time:** ~2-3 minutes

**Expected output:**
```
Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

lambda_function_name = "iam-scanner-lambda"
lambda_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:iam-scanner-lambda"
s3_bucket_name = "audit-reports-bucket-123456789012"
```

> 💾 **Save the output values** - you'll need them for running audits.

---

## 🎯 Basic Usage

### Your First IAM Audit

Let's audit an IAM role named `MyApplicationRole`:

```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyApplicationRole"}' \
  output.json
```

**View the response:**
```bash
cat output.json
```

**Expected response:**
```json
{
  "statusCode": 200,
  "body": {
    "message": "IAM audit completed successfully",
    "role_name": "MyApplicationRole",
    "report_location": "s3://audit-reports-bucket/iam-audit-reports/MyApplicationRole-20240320-143052.xlsx",
    "timestamp": "2024-03-20T14:30:52Z"
  }
}
```

### Download the Report

```bash
aws s3 cp s3://audit-reports-bucket/iam-audit-reports/MyApplicationRole-20240320-143052.xlsx ./
```

**Open the Excel file** and explore the 5 worksheets!

---

## ✅ Verification

### Verify Lambda Function

```bash
aws lambda get-function --function-name iam-scanner-lambda
```

Should return function details including runtime, memory, timeout.

### Verify S3 Bucket

```bash
aws s3 ls | grep audit-report
```

Should show your audit reports bucket.

### View Lambda Logs

```bash
aws logs tail /aws/lambda/iam-scanner-lambda --follow
```

### Check Terraform State

```bash
terraform output
```

Shows all deployed resource identifiers.

---

## 🎓 Next Steps

Now that you've deployed the utility and run your first audit, explore:

### Learn More
- 📖 **[Usage Guide](usage-guide.md)** - Advanced invocation methods, scheduling, batch audits
- 📊 **[Features](features.md)** - Detailed report structure and capabilities
- 🏗️ **[Architecture](architecture.md)** - System design and components
- 🎥 **[Videos](videos.md)** - Video tutorials

### Try These
1. **Audit multiple roles** in your account
2. **Set up scheduled audits** with EventBridge
3. **Integrate with CI/CD** pipelines
4. **Analyze risk findings** and implement least privilege

### Customize
- Increase Lambda memory/timeout for large roles
- Configure S3 lifecycle policies for report retention
- Add custom alerting with CloudWatch Alarms
- Export data to security tools (SIEM, compliance platforms)

---

<div align="center">

**Questions?** Review the [Usage Guide](usage-guide.md) or [Troubleshooting](usage-guide.md#troubleshooting)

[⬆ Back to Top](#-getting-started-guide)

</div>
