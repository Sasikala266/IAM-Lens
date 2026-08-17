# IAM Audit Utility (IAM-Lens)

> **Automated IAM Role & Policy Auditing Solution for AWS**

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.0-623CE4?logo=terraform)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20S3%20%7C%20IAM-FF9900?logo=amazon-aws)](https://aws.amazon.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)

## Overview

This project deploys an AWS Lambda function that scans IAM resources and generates audit reports. The reports are stored in an S3 bucket for analysis and compliance purposes.

## Architecture

The Terraform configuration creates the following resources:

### Key Questions Answered

During IAM access audits, you need answers to:
- ✅ **Which resources** can access **what services**?
- ✅ **What actions** are permitted?
- ✅ **What resource-level** constraints exist?
- ✅ **What security risks** are present (wildcards, overly permissive access)?
- ✅ **When** were permissions last used?

This utility provides **all answers in one place** with near-zero operational cost.

---

## Features

### 📊 Comprehensive Excel Reports

Each audit generates a **5-sheet Excel workbook** containing:

1. **Role Details** - High-level role configuration and metadata
2. **Detailed Permissions** - Granular breakdown of every permission (policies, services, actions, resources)
3. **Service Summary** - Access level aggregation (Read/Write/List/Delete/Admin per service)
4. **Risk Findings** - Security risk identification (wildcards, sensitive access, PassRole, etc.)
5. **Last Access** - Usage tracking via AWS Access Advisor

### 🔒 Built-in Security Analysis

Automatically detects:
- **Wildcard Permissions** (`*` in actions or resources)
- **Write & Delete Access** on critical services
- **PassRole Permissions** (privilege escalation risks)
- **Sensitive Service Access** (IAM, KMS, Secrets Manager, etc.)
- **Resource Constraint Violations** (overly broad access)
- **Cross-Account Access** patterns

### 💰 Near-Zero Cost Architecture

- ❌ No API Gateway
- ❌ No databases (RDS/DynamoDB)
- ❌ No running servers
- ✅ Pure serverless (Lambda + S3 only)
- ✅ Estimated cost: **< $1/month** for typical usage

---

## Quick Start

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

### Deploy in 3 Steps

```bash
# 1. Initialize Terraform
terraform init

# 2. Review deployment plan
terraform plan

# 3. Deploy infrastructure
terraform apply
```

### Run Your First Audit

```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyApplicationRole"}' \
  output.json
```

### Download the Report

```bash
aws s3 cp \
  s3://audit-reports-bucket/iam-audit-reports/MyApplicationRole-<timestamp>.xlsx \
  ./audit-report.xlsx
```

---

## Documentation

### 📚 Complete Documentation Set

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** | Detailed system design, data flow, and component specifications |
| **[FEATURES.md](docs/FEATURES.md)** | Comprehensive feature list and report structure |
| **[USAGE.md](docs/USAGE.md)** | Step-by-step usage guide with examples |
| **README.md** | This file - overview and quick start |

---

## Usage Examples

**Audit a single IAM role:**
```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyApplicationRole"}' \
  output.json
```

For more examples, see [docs/USAGE.md](docs/USAGE.md)

---

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
│   └── requirements.txt# Python dependencies
├── docs/
│   ├── ARCHITECTURE.md # Detailed architecture
│   ├── FEATURES.md     # Feature documentation
│   └── USAGE.md        # Usage guide
└── README.md           # This file

### 4. Invoke the Lambda Function
---

## Security Considerations

### ✅ Security Best Practices Implemented

| Feature | Implementation |
|---------|----------------|
| **S3 Encryption** | AES-256 server-side encryption enabled |
| **Public Access** | All public access blocked on S3 bucket |
| **IAM Permissions** | Least privilege - read-only IAM access |
| **Logging** | CloudWatch Logs enabled for audit trail |
| **Versioning** | S3 versioning enabled for report history |
| **No Credentials** | No hardcoded credentials (CWE-798) |

### IAM Permissions Granted to Lambda

**Read-Only IAM Access:**
- `iam:GetRole`, `iam:GetPolicy`, `iam:GetPolicyVersion`
- `iam:ListRoles`, `iam:ListPolicies`
- `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies`
```
**S3 Access** (scoped to audit bucket only):
- `s3:PutObject`, `s3:GetObject`, `s3:ListBucket`

---
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

---

## Troubleshooting

### View Lambda Logs

```bash
aws logs tail /aws/lambda/iam-scanner-lambda --follow
```

For detailed troubleshooting, see [docs/USAGE.md](docs/USAGE.md#troubleshooting)

---

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with clear descriptions

---

## License

This project is provided as-is for educational and deployment purposes.
