# IAM Audit Utility - Architecture Documentation

## Overview

The IAM Audit Utility is a serverless solution designed to automate IAM role and policy auditing in AWS. It eliminates the need for manual audits using multiple AWS services (IAM Console, APIs, CloudTrail, Access Advisor, Access Analyzer) by consolidating all audit information in a single, comprehensive Excel report.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          IAM Audit Utility Flow                          │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐
  │   User/      │
  │  Scheduler   │
  └──────┬───────┘
         │
         │ 1. Invoke Lambda with
         │    Test Event (Role ARN/Policy ARN)
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │              AWS Lambda Function                         │
  │            (Python 3.11 - 512MB RAM)                     │
  │                                                           │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 1: Input Processing                          │  │
  │  │  - Parse role_name or policy_arn from event       │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 2: IAM Data Fetching (via boto3)            │  │
  │  │  - Get Role details                               │  │
  │  │  - Get Managed Policies                           │  │
  │  │  - Get Inline Policies                            │  │
  │  │  - Get Default Policy Versions                    │  │
  │  │  - Get Last Access information                    │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 3: Enrichment & Parsing                      │  │
  │  │  - Parse policy JSON documents                     │  │
  │  │  - Classify AWS services                           │  │
  │  │  - Classify actions (Read/Write/List/Delete/Admin) │  │
  │  │  - Identify resource-level specifications          │  │
  │  │  - Detect risk patterns (wildcards, pass roles)    │  │
  │  │  - Extract condition constraints                   │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 4: Report Generation (OpenPyXL)             │  │
  │  │  - Create 5 Excel sheets:                         │  │
  │  │    1. Role Details                                │  │
  │  │    2. Detailed Permissions                        │  │
  │  │    3. Service Summary                             │  │
  │  │    4. Risk Findings                               │  │
  │  │    5. Last Access                                 │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 5: S3 Upload                                │  │
  │  │  - Upload Excel report to S3 bucket               │  │
  │  │  - Timestamp-based filename                       │  │
  │  └────────────────────────────────────────────────────┘  │
  └──────────────────────┬───────────────────────────────────┘
                         │
                         │ 2. Store Report
                         │
                         ▼
              ┌──────────────────────┐
              │    Amazon S3         │
              │  Audit Reports       │
              │  ┌────────────────┐  │
              │  │ Reports/       │  │
              │  │  role1.xlsx    │  │
              │  │  role2.xlsx    │  │
              │  └────────────────┘  │
              └──────────────────────┘

         ┌───────────────────────────────────┐
         │      AWS Services Queried         │
         │  (Read-Only Access)               │
         │                                   │
         │  • IAM Roles                      │
         │  • IAM Policies                   │
         │  • Policy Versions                │
         │  • Access Advisor (Last Access)   │
         └───────────────────────────────────┘
```

## Component Details

### 1. AWS Lambda Function

**Purpose**: Core processing engine for IAM audit analysis

**Specifications**:
- Runtime: Python 3.11
- Memory: 512 MB
- Timeout: 5 minutes (300 seconds)
- Ephemeral Storage: 512 MB

**Key Libraries**:
- `boto3`: AWS SDK for Python (IAM API interactions)
- `openpyxl`: Excel file generation
- Standard Python libraries for JSON parsing and data processing

**Environment Variables**:
- `S3_BUCKET_NAME`: Target S3 bucket for report storage
- `REPORT_PREFIX`: Prefix path for organizing reports

### 2. Amazon S3 Bucket

**Purpose**: Secure storage for generated audit reports

**Configuration**:
- Versioning: Enabled (track report history)
- Encryption: Server-side encryption (AES-256)
- Public Access: Blocked (security best practice)
- Lifecycle: Configurable retention policies

### 3. IAM Role & Permissions

**Lambda Execution Role Permissions**:
- **CloudWatch Logs**: Write logs for monitoring and debugging
- **S3 Access**: Put/Get objects in the audit reports bucket
- **IAM Read-Only**: Query IAM resources without modification capability
  - GetRole, ListRoles
  - GetPolicy, GetPolicyVersion
  - ListAttachedRolePolicies, ListRolePolicies
  - GetAccountSummary

**Security Principle**: Least privilege - read-only IAM access, no modification capabilities

## Data Flow

### Input Stage
1. User invokes Lambda with test event containing:
   - `role_name`: IAM role to audit (required)
   - `policy_arn`: Specific policy ARN (optional)

### Processing Stage
2. Lambda function retrieves IAM configuration:
   - Role trust policies and permissions
   - Attached managed policies (AWS and custom)
   - Inline policies
   - Policy document versions

3. Data enrichment and classification:
   - Parse policy JSON structures
   - Classify AWS services and actions
   - Determine access types (Read/Write/List/Delete/Admin)
   - Identify security risks and wildcards
   - Extract resource-level constraints

### Output Stage
4. Generate comprehensive Excel report with multiple sheets
5. Upload report to S3 with timestamp-based naming
6. Return success response with S3 location

## Cost Model

**Near-Zero Cost Architecture**:
- No API Gateway (no per-request charges)
- No databases (no RDS/DynamoDB costs)
- No running servers (pure serverless)
- Pay only for Lambda execution time and S3 storage
- Estimated cost: < $1/month for typical usage patterns
