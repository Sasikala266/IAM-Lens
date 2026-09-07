# IAM Audit Utility - Usage Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment](#deployment)
3. [Basic Usage](#basic-usage)
4. [Input Formats](#input-formats)
5. [Invoking the Lambda Function](#invoking-the-lambda-function)
6. [Retrieving Reports](#retrieving-reports)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before using the IAM Audit Utility, ensure you have:

### Required Tools
- **Terraform** >= 1.0 ([Installation Guide](https://developer.hashicorp.com/terraform/downloads))
- **AWS CLI** >= 2.0 ([Installation Guide](https://aws.amazon.com/cli/))
- **AWS Account** with appropriate permissions

### Required AWS Permissions

To deploy the infrastructure, your AWS credentials need:
- `iam:CreateRole`, `iam:CreatePolicy`, `iam:AttachRolePolicy`
- `lambda:CreateFunction`, `lambda:UpdateFunctionCode`
- `s3:CreateBucket`, `s3:PutBucketPolicy`
- `logs:CreateLogGroup`

### AWS Configuration

Configure AWS credentials:

```bash
# Option 1: AWS CLI configuration
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export AWS_DEFAULT_REGION="us-east-1"
```

---

## Deployment

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd iam-audit-utility
```

### Step 2: Review Configuration

Check default values in `variables.tf` or create `terraform.tfvars`:

```hcl
# terraform.tfvars (optional)
aws_region          = "us-east-1"
lambda_function_name = "iam-scanner-lambda"
lambda_memory_size   = 512
lambda_timeout       = 300

tags = {
  Environment = "Production"
  Project     = "IAM Audit"
  ManagedBy   = "Terraform"
}
```

### Step 3: Initialize Terraform

```bash
terraform init
```

### Step 4: Review Deployment Plan

```bash
terraform plan
```

Review the resources that will be created:
- Lambda function
- S3 bucket
- IAM roles and policies
- CloudWatch log group

### Step 5: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted to confirm deployment.

### Step 6: Verify Deployment

```bash
# Check Lambda function
aws lambda get-function --function-name iam-scanner-lambda

# Check S3 bucket
aws s3 ls | grep audit-report

# View Terraform outputs
terraform output
```

---

## Basic Usage

### Quick Start Example

Audit an IAM role named `MyApplicationRole`:

```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyApplicationRole"}' \
  output.json

cat output.json
```

**Expected Response**:
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

---

## Input Formats
### Structured Format (Recommended)


### Option 1: Audit by Role Name

**Use Case**: Audit a specific IAM role

```json
{
  "targets": [
    {
      "type": "role",
      "name": "MyApplicationRole"
    }
  ]
  "role_name": "MyApplicationRole"
}
```
**Note**: The structured `targets` format is the recommended approach.


### Option 2: Audit by Policy ARN

**Use Case**: Audit a specific managed policy

```json
{
  "targets": [
    {
      "type": "policy",
      "arn": "arn:aws:iam::123456789012:policy/MyCustomPolicy"
    }
  ]
  "policy_arn": "arn:aws:iam::123456789012:policy/MyCustomPolicy"
}
```
### Option 3: Audit Multiple Targets (Roles and Policies)
### Option 3: Audit Role with Specific Policy
**Use Case**: Audit multiple roles and policies in one execution
**Use Case**: Focus on a particular policy attached to a role

```json
  "targets": [
    {
      "type": "role",
      "name": "MyApplicationRole"
    },
    {
      "type": "policy",
      "arn": "arn:aws:iam::123456789012:policy/MyPolicy"
    },
    {
      "type": "role",
      "name": "MyLambdaRole"
    }
  ]
  "policy_arn": "arn:aws:iam::123456789012:policy/MyCustomPolicy"
}
```
### Legacy Format (Still Supported)
### Option 4: Batch Audit (Multiple Roles)
### Option 4: Batch Audit (Multiple Roles - Legacy)

**Use Case**: Audit multiple roles using the legacy format
**Use Case**: Audit multiple roles in one execution

```json
{
  "role_names": [
    "MyApplicationRole",
    "MyLambdaRole",
    "MyEC2Role"
  ]
}
```

**Note**: The legacy `role_names` format is still supported for backward compatibility, but the structured `targets` format is recommended for new implementations as it supports both roles and policies.

---

## Input Format Examples

### Example 1: New Structured Format

```json
{
  "output_bucket": "my-audit-bucket",
  "targets": [
    {
      "type": "role",
      "name": "MyApplicationRole"
    },
    {
      "type": "policy",
      "arn": "arn:aws:iam::123456789012:policy/MyCustomPolicy"
    }
  ],
  "include_last_access": true,
  "include_cloudtrail_usage": true
}
```

### Example 2: Legacy Format (Backward Compatible)

```json
{
  "output_bucket": "my-audit-bucket",
  "role_names": [
    "MyApplicationRole",
    "MyLambdaRole"
  ],
  "include_last_access": true,
  "include_cloudtrail_usage": true
}

---

## Invoking the Lambda Function

### Method 1: AWS CLI

**Basic Invocation**:
```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyRole"}' \
  output.json
```

**With JSON File**:
```bash
# Create input file
cat > input.json << EOF
{
  "role_name": "MyApplicationRole"
}
EOF

# Invoke Lambda
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload file://input.json \
  output.json
```

**Asynchronous Invocation**:
```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --invocation-type Event \
  --payload '{"role_name": "MyRole"}' \
  output.json
```

### Method 2: AWS Console

1. Navigate to **AWS Lambda Console**
2. Select `iam-scanner-lambda` function
3. Click **Test** tab
4. Create a new test event:
   - **Event name**: `TestAudit`
   - **Event JSON**:
     ```json
     {
       "role_name": "MyApplicationRole"
     }
     ```
5. Click **Test** button
6. View execution results and logs

### Method 3: AWS SDK (Python)

```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='iam-scanner-lambda',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'role_name': 'MyApplicationRole'
    })
)

result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))
```

### Method 4: Scheduled Execution (EventBridge)

Create a scheduled audit that runs weekly:

```bash
# Create EventBridge rule
aws events put-rule \
  --name weekly-iam-audit \
  --schedule-expression "cron(0 9 ? * MON *)"

# Add Lambda as target
aws events put-targets \
  --rule weekly-iam-audit \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:iam-scanner-lambda","Input"='{"role_name":"MyRole"}'

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name iam-scanner-lambda \
  --statement-id weekly-audit \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT:rule/weekly-iam-audit
```

---

## Retrieving Reports

### List Available Reports

```bash
aws s3 ls s3://audit-reports-bucket/iam-audit-reports/
```

### Download Specific Report

```bash
aws s3 cp \
  s3://audit-reports-bucket/iam-audit-reports/MyRole-20240320-143052.xlsx \
  ./reports/
```

### Download All Reports

```bash
aws s3 sync \
  s3://audit-reports-bucket/iam-audit-reports/ \
  ./reports/
```

### Generate Pre-Signed URL (Temporary Access)

```bash
aws s3 presign \
  s3://audit-reports-bucket/iam-audit-reports/MyRole-20240320-143052.xlsx \
  --expires-in 3600
```

Share the generated URL for temporary access (valid for 1 hour).

---

## Advanced Usage

### 1. Audit All Roles in Account

Create a wrapper script to audit all roles:

```bash
#!/bin/bash

# Get all role names
ROLES=$(aws iam list-roles --query 'Roles[*].RoleName' --output text)

# Audit each role
for ROLE in $ROLES; do
  echo "Auditing role: $ROLE"
  aws lambda invoke \
    --function-name iam-scanner-lambda \
    --payload "{\"role_name\": \"$ROLE\"}" \
    --invocation-type Event \
    output-$ROLE.json
  sleep 2  # Rate limiting
done

echo "All audits initiated"
```

### 2. Compare Role Permissions

```bash
# Audit two roles
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "Role1"}' \
  output1.json

aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "Role2"}' \
  output2.json

# Download reports
aws s3 cp s3://audit-reports-bucket/iam-audit-reports/Role1-*.xlsx ./role1.xlsx
aws s3 cp s3://audit-reports-bucket/iam-audit-reports/Role2-*.xlsx ./role2.xlsx

# Compare in Excel or use spreadsheet comparison tools
```

### 3. Integration with CI/CD Pipeline

**GitHub Actions Example**:

```yaml
name: Weekly IAM Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Run IAM Audit
        run: |
          aws lambda invoke \
            --function-name iam-scanner-lambda \
            --payload '{"role_name": "ProductionRole"}' \
            output.json
          
          cat output.json

      - name: Download Report
        run: |
          REPORT=$(aws s3 ls s3://audit-reports-bucket/iam-audit-reports/ --recursive | sort | tail -n 1 | awk '{print $4}')
          aws s3 cp s3://audit-reports-bucket/$REPORT ./audit-report.xlsx

      - name: Upload Artifact
        uses: actions/upload-artifact@v2
        with:
          name: iam-audit-report
          path: audit-report.xlsx
```

### 4. Filtering and Analysis

After downloading reports, use Python for automated analysis:

```python
import openpyxl

# Load report
wb = openpyxl.load_workbook('audit-report.xlsx')

# Analyze Risk Findings sheet
risk_sheet = wb['Risk Findings']

high_risks = []
for row in risk_sheet.iter_rows(min_row=2, values_only=True):
    if row[1] == 'High' or row[1] == 'Critical':
        high_risks.append({
            'risk_type': row[0],
            'severity': row[1],
            'service': row[2],
            'description': row[5]
        })

print(f"Found {len(high_risks)} high/critical risks")
for risk in high_risks:
    print(f"- {risk['risk_type']}: {risk['description']}")
```

---

## Troubleshooting

### Issue 1: Lambda Timeout

**Symptom**: Lambda times out before completing audit

**Solution**: Increase timeout in `variables.tf`:
```hcl
lambda_timeout = 600  # 10 minutes
```

Then redeploy:
```bash
terraform apply
```

---

### Issue 2: Insufficient IAM Permissions

**Symptom**: `AccessDenied` errors in Lambda logs

**Solution**: Verify Lambda execution role has required permissions:
```bash
aws iam get-role-policy \
  --role-name iam-scanner-lambda-role \
  --policy-name iam-scanner-lambda-policy
```

Required IAM actions:
- `iam:GetRole`
- `iam:GetPolicy`
- `iam:GetPolicyVersion`
- `iam:ListAttachedRolePolicies`
- `iam:ListRolePolicies`
- `iam:GenerateServiceLastAccessedDetails` (for Last Access tab)
- `iam:GetServiceLastAccessedDetails` (for Last Access tab)
- `cloudtrail:LookupEvents` (for Role Usage CloudTrail tab)

---

### Issue 3: S3 Upload Failed

**Symptom**: Report generated but not uploaded to S3

**Solution**: 
1. Check S3 bucket exists:
   ```bash
   aws s3 ls s3://audit-reports-bucket/
   ```

2. Verify Lambda has S3 permissions:
   ```bash
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::ACCOUNT:role/iam-scanner-lambda-role \
     --action-names s3:PutObject \
     --resource-arns arn:aws:s3:::audit-reports-bucket/*
   ```

---

### Issue 4: Role Not Found

**Symptom**: `NoSuchEntity` error when auditing role

**Solution**: Verify role name is correct:
```bash
aws iam get-role --role-name MyApplicationRole
```

List all available roles:
```bash
aws iam list-roles --query 'Roles[*].RoleName' --output table
```

---

### Issue 5: Memory Limit Exceeded

**Symptom**: Lambda runs out of memory for large roles

**Solution**: Increase memory in `variables.tf`:
```hcl
lambda_memory_size = 1024  # 1 GB
```

---

### Viewing Logs

**CloudWatch Logs**:
```bash
# View recent logs
aws logs tail /aws/lambda/iam-scanner-lambda --follow

# View specific log stream
aws logs get-log-events \
  --log-group-name /aws/lambda/iam-scanner-lambda \
  --log-stream-name '2024/03/20/[$LATEST]abc123'
```

**Enable Debug Logging**:

Update Lambda environment variable:
```bash
aws lambda update-function-configuration \
  --function-name iam-scanner-lambda \
  --environment 'Variables={S3_BUCKET_NAME=audit-reports-bucket,REPORT_PREFIX=iam-audit-reports,DEBUG=true}'
```

---

## Best Practices

1. **Schedule Regular Audits**: Use EventBridge to run weekly audits
2. **Retention Policy**: Configure S3 lifecycle rules to archive old reports
3. **Cost Monitoring**: Set up AWS Budgets to track Lambda and S3 costs
4. **Access Control**: Limit who can invoke the Lambda function
5. **Report Review**: Establish a process for reviewing risk findings
6. **Version Control**: Keep audit reports in version control for trend analysis
7. **Alerting**: Set up CloudWatch alarms for Lambda errors
8. **Backup**: Enable S3 versioning for report history

---

## Next Steps

- Review [FEATURES.md](FEATURES.md) for detailed report structure
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Customize the Lambda function for your specific audit requirements
- Integrate with your organization's compliance workflow

