<div align="center">

# 📖 Usage Guide

### Advanced Usage, Input Formats, and Troubleshooting

[← Back to Main](../README.md) | [Getting Started →](getting-started.md) | [Features →](features.md)

</div>

---

## 📋 Table of Contents

1. [Input Formats](#-input-formats)
2. [Invoking the Lambda Function](#-invoking-the-lambda-function)
3. [Retrieving Reports](#-retrieving-reports)
4. [Advanced Usage](#-advanced-usage)
5. [Troubleshooting](#-troubleshooting)
6. [Best Practices](#-best-practices)

---

## 📝 Input Formats

The Lambda function accepts different input formats depending on your audit needs.

### Option 1: Audit by Role Name

**Use Case:** Audit a specific IAM role and all its attached policies.

```json
{
  "role_name": "MyApplicationRole"
}
```

**What gets audited:**
- Role details (ARN, creation date, trust policy)
- All AWS managed policies attached to the role
- All customer managed policies attached to the role
- All inline policies embedded in the role
- Last access information for all services

### Option 2: Audit by Policy ARN

**Use Case:** Audit a specific managed policy (AWS or customer managed).

```json
{
  "policy_arn": "arn:aws:iam::123456789012:policy/MyCustomPolicy"
}
```

**What gets audited:**
- Policy details and metadata
- All permissions in the policy document
- Services and actions granted
- Risk analysis of permissions

### Option 3: Audit Role with Specific Policy Filter

**Use Case:** Focus audit on a particular policy attached to a role.

```json
{
  "role_name": "MyApplicationRole",
  "policy_arn": "arn:aws:iam::123456789012:policy/MyCustomPolicy"
}
```

### Option 4: Batch Audit Multiple Roles

**Use Case:** Audit multiple roles in a single execution.

```json
{
  "role_names": [
    "MyApplicationRole",
    "MyLambdaRole",
    "MyEC2Role"
  ]
}
```

**Note:** Generates separate reports for each role.

---

## 🔧 Invoking the Lambda Function

### Method 1: AWS CLI (Recommended)

#### Basic Invocation

```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyRole"}' \
  output.json

cat output.json
```

#### Using JSON File Input

```bash
# Create input file
cat > input.json << EOF
{
  "role_name": "MyApplicationRole"
}
EOF

# Invoke Lambda with file
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload file://input.json \
  output.json
```

#### Asynchronous Invocation

For long-running audits, use asynchronous invocation:

```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --invocation-type Event \
  --payload '{"role_name": "MyRole"}' \
  output.json
```

> 💡 **Async invocation** returns immediately. Check CloudWatch Logs or S3 for results.

#### Specify AWS Region

```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --region us-west-2 \
  --payload '{"role_name": "MyRole"}' \
  output.json
```

---

### Method 2: AWS Console

**Step-by-step:**

1. **Navigate to Lambda Console**
   - Go to AWS Console → Lambda
   - Search for `iam-scanner-lambda`
   - Click on the function name

2. **Create Test Event**
   - Click the **Test** tab
   - Click **Create new event**
   - **Event name**: `TestRoleAudit`
   - **Event JSON**:
     ```json
     {
       "role_name": "MyApplicationRole"
     }
     ```
   - Click **Save**

3. **Run Test**
   - Click **Test** button
   - View execution results in the console
   - Check **Execution result** tab for response
   - Check **Logs** tab for detailed execution logs

4. **Download Report**
   - Copy the S3 path from the response
   - Navigate to S3 console
   - Download the Excel file

---

### Method 3: AWS SDK (Python)

```python
import boto3
import json

# Initialize Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

# Prepare payload
payload = {
    'role_name': 'MyApplicationRole'
}

# Invoke Lambda function
response = lambda_client.invoke(
    FunctionName='iam-scanner-lambda',
    InvocationType='RequestResponse',  # Synchronous
    Payload=json.dumps(payload)
)

# Parse response
result = json.loads(response['Payload'].read())
print(json.dumps(result, indent=2))

# Extract S3 location
if result.get('statusCode') == 200:
    report_location = result['body']['report_location']
    print(f"Report available at: {report_location}")
```

---

### Method 4: AWS SDK (JavaScript/Node.js)

```javascript
const AWS = require('aws-sdk');

const lambda = new AWS.Lambda({ region: 'us-east-1' });

const params = {
  FunctionName: 'iam-scanner-lambda',
  InvocationType: 'RequestResponse',
  Payload: JSON.stringify({
    role_name: 'MyApplicationRole'
  })
};

lambda.invoke(params, (err, data) => {
  if (err) {
    console.error('Error:', err);
  } else {
    const result = JSON.parse(data.Payload);
    console.log('Result:', JSON.stringify(result, null, 2));
  }
});
```

---

### Method 5: Scheduled Execution (EventBridge)

Set up automatic audits on a schedule:

#### Create Weekly Audit Schedule

```bash
# Create EventBridge rule (every Monday at 9 AM UTC)
aws events put-rule \
  --name weekly-iam-audit \
  --schedule-expression "cron(0 9 ? * MON *)" \
  --state ENABLED \
  --description "Weekly IAM role audit"

# Get Lambda function ARN
LAMBDA_ARN=$(aws lambda get-function \
  --function-name iam-scanner-lambda \
  --query 'Configuration.FunctionArn' \
  --output text)

# Add Lambda as target
aws events put-targets \
  --rule weekly-iam-audit \
  --targets "Id"="1","Arn"="$LAMBDA_ARN","Input"='{"role_name":"ProductionRole"}'

# Grant EventBridge permission to invoke Lambda
aws lambda add-permission \
  --function-name iam-scanner-lambda \
  --statement-id weekly-audit-event \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:REGION:ACCOUNT_ID:rule/weekly-iam-audit
```

#### Schedule Expressions Examples

```bash
# Every day at 2 AM UTC
"cron(0 2 * * ? *)"

# Every Monday at 9 AM UTC
"cron(0 9 ? * MON *)"

# First day of every month at 8 AM UTC
"cron(0 8 1 * ? *)"

# Every hour
"rate(1 hour)"

# Every 12 hours
"rate(12 hours)"
```

---

## 📥 Retrieving Reports

### List All Reports

```bash
aws s3 ls s3://audit-reports-bucket/iam-audit-reports/
```

**Output:**
```
2024-03-20 14:30:52    245678 MyRole-20240320-143052.xlsx
2024-03-19 10:15:33    189234 LambdaRole-20240319-101533.xlsx
2024-03-18 16:45:21    334567 EC2Role-20240318-164521.xlsx
```

### Download Specific Report

```bash
aws s3 cp \
  s3://audit-reports-bucket/iam-audit-reports/MyRole-20240320-143052.xlsx \
  ./reports/
```

### Download All Reports

```bash
# Create local directory
mkdir -p ./reports

# Sync all reports
aws s3 sync \
  s3://audit-reports-bucket/iam-audit-reports/ \
  ./reports/
```

### Generate Pre-Signed URL (Temporary Access)

Create a temporary download link valid for 1 hour:

```bash
aws s3 presign \
  s3://audit-reports-bucket/iam-audit-reports/MyRole-20240320-143052.xlsx \
  --expires-in 3600
```

**Output:**
```
https://audit-reports-bucket.s3.amazonaws.com/iam-audit-reports/MyRole-20240320-143052.xlsx?X-Amz-Algorithm=...
```

Share this URL with stakeholders for temporary access (no AWS credentials needed).

### Download Latest Report

```bash
# Get the most recent report
LATEST_REPORT=$(aws s3 ls s3://audit-reports-bucket/iam-audit-reports/ \
  | sort | tail -n 1 | awk '{print $4}')

# Download it
aws s3 cp \
  s3://audit-reports-bucket/iam-audit-reports/$LATEST_REPORT \
  ./latest-report.xlsx
```

---

## 🚀 Advanced Usage

### 1. Audit All Roles in Account

Create a bash script to audit every IAM role:

```bash
#!/bin/bash
# audit-all-roles.sh

# Get all role names
ROLES=$(aws iam list-roles --query 'Roles[*].RoleName' --output text)

# Count roles
ROLE_COUNT=$(echo $ROLES | wc -w)
echo "Found $ROLE_COUNT roles to audit"

# Audit each role
for ROLE in $ROLES; do
  echo "Auditing role: $ROLE"
  
  aws lambda invoke \
    --function-name iam-scanner-lambda \
    --payload "{\"role_name\": \"$ROLE\"}" \
    --invocation-type Event \
    output-$ROLE.json
  
  # Rate limiting (avoid throttling)
  sleep 2
done

echo "All $ROLE_COUNT audit requests submitted"
echo "Check S3 bucket for reports in a few minutes"
```

**Run the script:**
```bash
chmod +x audit-all-roles.sh
./audit-all-roles.sh
```

### 2. Compare Role Permissions

Audit two roles and compare their permissions:

```bash
# Audit both roles
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "Role1"}' \
  output1.json

aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "Role2"}' \
  output2.json

# Wait for reports to be generated
sleep 30

# Download both reports
aws s3 cp s3://audit-reports-bucket/iam-audit-reports/Role1-*.xlsx ./role1.xlsx
aws s3 cp s3://audit-reports-bucket/iam-audit-reports/Role2-*.xlsx ./role2.xlsx

# Open both in Excel for side-by-side comparison
```

### 3. Integration with CI/CD Pipeline

#### GitHub Actions Example

```yaml
name: Weekly IAM Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:       # Manual trigger

jobs:
  audit-iam-roles:
    runs-on: ubuntu-latest
    
    steps:
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v2
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
          # Get the latest report
          REPORT=$(aws s3 ls s3://audit-reports-bucket/iam-audit-reports/ \
            --recursive | sort | tail -n 1 | awk '{print $4}')
          
          # Download it
          aws s3 cp s3://audit-reports-bucket/$REPORT ./audit-report.xlsx

      - name: Upload Report as Artifact
        uses: actions/upload-artifact@v3
        with:
          name: iam-audit-report
          path: audit-report.xlsx
          retention-days: 30
```

### 4. Automated Risk Analysis

Use Python to automatically analyze risk findings:

```python
import openpyxl
import sys

# Load report
wb = openpyxl.load_workbook('audit-report.xlsx')
risk_sheet = wb['Risk Findings']

# Count risks by severity
severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}

for row in risk_sheet.iter_rows(min_row=2, values_only=True):
    severity = row[1]  # Severity column
    if severity in severity_counts:
        severity_counts[severity] += 1

# Print summary
print("IAM Audit Risk Summary")
print("=" * 40)
for severity, count in severity_counts.items():
    print(f"{severity}: {count}")

# Exit with error if critical risks found
if severity_counts['Critical'] > 0:
    print(f"\n⚠️  Found {severity_counts['Critical']} CRITICAL risks!")
    sys.exit(1)
```

### 5. Filter Reports by Date Range

Download reports from a specific date range:

```bash
# List reports from March 2024
aws s3 ls s3://audit-reports-bucket/iam-audit-reports/ \
  | grep "202403"

# Download all reports from March 2024
aws s3 sync \
  s3://audit-reports-bucket/iam-audit-reports/ \
  ./march-reports/ \
  --exclude "*" \
  --include "*202403*"
```

---

## 🛠️ Troubleshooting

### Issue 1: Lambda Timeout

**Symptom:** Lambda function times out before completing the audit.

**Cause:** Large roles with many policies take longer to process.

**Solution:** Increase timeout in Terraform configuration:

```hcl
# variables.tf or terraform.tfvars
lambda_timeout = 600  # 10 minutes
```

Apply changes:
```bash
terraform apply
```

---

### Issue 2: Insufficient IAM Permissions

**Symptom:** `AccessDenied` errors in Lambda logs or output.

**Cause:** Lambda execution role lacks required IAM permissions.

**Solution:** Verify Lambda role has these permissions:

```bash
aws iam get-role-policy \
  --role-name iam-scanner-lambda-role \
  --policy-name iam-scanner-lambda-policy
```

**Required IAM actions:**
- `iam:GetRole`
- `iam:GetPolicy`
- `iam:GetPolicyVersion`
- `iam:ListAttachedRolePolicies`
- `iam:ListRolePolicies`
- `iam:GetRolePolicy`
- `iam:GenerateServiceLastAccessedDetails`
- `iam:GetServiceLastAccessedDetails`

---

### Issue 3: S3 Upload Failed

**Symptom:** Report generated but not uploaded to S3.

**Solution:**

1. **Check S3 bucket exists:**
   ```bash
   aws s3 ls s3://audit-reports-bucket/
   ```

2. **Verify Lambda has S3 write permissions:**
   ```bash
   aws iam simulate-principal-policy \
     --policy-source-arn arn:aws:iam::ACCOUNT_ID:role/iam-scanner-lambda-role \
     --action-names s3:PutObject \
     --resource-arns arn:aws:s3:::audit-reports-bucket/*
   ```

3. **Check CloudWatch Logs for S3 errors:**
   ```bash
   aws logs tail /aws/lambda/iam-scanner-lambda --follow
   ```

---

### Issue 4: Role Not Found

**Symptom:** `NoSuchEntity` error when auditing a role.

**Solution:**

1. **Verify role name is correct:**
   ```bash
   aws iam get-role --role-name MyApplicationRole
   ```

2. **List all available roles:**
   ```bash
   aws iam list-roles --query 'Roles[*].RoleName' --output table
   ```

3. **Check for typos in role name** (case-sensitive!)

---

### Issue 5: Memory Limit Exceeded

**Symptom:** Lambda runs out of memory for roles with many policies.

**Solution:** Increase memory allocation:

```hcl
# variables.tf or terraform.tfvars
lambda_memory_size = 1024  # 1 GB
```

Apply changes:
```bash
terraform apply
```

---

### Viewing CloudWatch Logs

**View recent logs (live tail):**
```bash
aws logs tail /aws/lambda/iam-scanner-lambda --follow
```

**View specific time range:**
```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/iam-scanner-lambda \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"
```

**Enable debug logging:**
```bash
aws lambda update-function-configuration \
  --function-name iam-scanner-lambda \
  --environment 'Variables={DEBUG=true}'
```

---

## ✅ Best Practices

### 1. Schedule Regular Audits
Use EventBridge to run audits automatically:
- **Weekly**: For production roles
- **Monthly**: For development/staging roles
- **After changes**: Trigger audits on IAM policy modifications

### 2. Configure S3 Lifecycle Policies
Set up retention policies to manage report storage costs:

```bash
# Transition reports to cheaper storage after 30 days
# Delete reports after 90 days
```

### 3. Monitor Lambda Execution
Set up CloudWatch alarms for:
- Lambda errors
- Execution duration approaching timeout
- Throttling events

### 4. Review Reports Regularly
Establish a process:
- Review high/critical risk findings immediately
- Quarterly reviews of all role permissions
- Document remediation actions

### 5. Version Control
Store reports in version control (Git) for:
- Trend analysis over time
- Comparing permission changes
- Compliance audit trails

### 6. Access Control
Limit who can:
- Invoke the Lambda function
- Access S3 reports
- Modify Lambda configuration

### 7. Cost Monitoring
Set up AWS Budgets to track:
- Lambda invocation costs
- S3 storage costs
- Data transfer costs

### 8. Backup Reports
Enable S3 versioning for:
- Recover accidentally deleted reports
- Maintain historical audit records

---

<div align="center">

**Need Help?** Check [Getting Started](getting-started.md) or [Features](features.md)

[⬆ Back to Top](#-usage-guide)

</div>
