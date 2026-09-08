# IAM Audit Utility - Architecture Documentation

## Overview

The IAM Audit Utility is a serverless solution designed to automate IAM role, policy, and user auditing in AWS. It eliminates the need for manual audits using multiple AWS services (IAM Console, APIs, CloudTrail, Access Advisor) by consolidating all audit information in a single, comprehensive Excel report.

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
         │    Test Event (Targets: Roles/Policies/Users)
         │    {
         │      "targets": [{"type": "role", "name": "..."}]
         │    }
         │
         ▼
  ┌──────────────────────────────────────────────────────────┐
  │              AWS Lambda Function                         │
  │            (Python 3.11 - 512MB RAM)                     │
  │                                                           │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 1: Input Processing                          │  │
  │  │  - Parse targets array (roles/policies/users)     │  │
  │  │  - Support legacy format for backward compat      │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 2: IAM Data Fetching (via boto3)            │  │
  │  │  - Get Role details                               │  │
  │  │  - Get User details                               │  │
  │  │  - Get Managed Policies                           │  │
  │  │  - Get Inline Policies                            │  │
  │  │  - Get Default Policy Versions                    │  │
  │  │  - Get Last Access information                    │  │
  │  │  - Query CloudTrail for usage patterns            │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 3: Enrichment & Parsing                      │  │
  │  │  - Parse policy JSON documents                     │  │
  │  │  - Classify AWS services                           │  │
  │  │  - Classify actions (Read/Write/List/Delete/Admin) │  │
  │  │  - Identify resource-level specifications          │  │
  │  │  - Parse CloudTrail events for activity tracking   │  │
  │  │  - Detect risk patterns (wildcards, pass roles)    │  │
  │  │  - Extract condition constraints                   │  │
  │  └────────────────────────────────────────────────────┘  │
  │                        │                                  │
  │                        ▼                                  │
  │  ┌────────────────────────────────────────────────────┐  │
  │  │  Step 4: Report Generation (OpenPyXL)             │  │
  │  │  - Create Excel report (format varies by type):   │  │
  │  │    Roles & Users (5 sheets):                      │  │
  │  │    1. Entity Details                              │  │
  │  │    2. Detailed Permissions                        │  │
  │  │    3. Service Summary                             │  │
  │  │    4. Risk Findings                               │  │
  │  │    5. Last Access                                 │  │
  │  │    Policies (3 sheets): Permissions, Summary, Risks│  │
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
  │  │ iam-audit-reports/ │
  │  │  Role1_*.xlsx    │
  │  │  Policy1_*.xlsx  │
  │  │  User1_*.xlsx    │
              │  └────────────────┘  │
              └──────────────────────┘

         ┌───────────────────────────────────┐
         │      AWS Services Queried         │
         │  (Read-Only Access)               │
         │                                   │
         │  • IAM Roles                      │
         │  • IAM Policies                   │
         │  • Policy Versions                │
  │  • IAM Users                      │
  │  • CloudTrail Events              │
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
- **IAM Read-Only**: Query IAM resources (no modification capability)
  - Role operations: GetRole, ListRoles, ListAttachedRolePolicies, ListRolePolicies, GetRolePolicy
  - Policy operations: GetPolicy, GetPolicyVersion, ListPolicies
  - User operations: GetUser, ListUsers, ListAttachedUserPolicies, ListUserPolicies, GetUserPolicy
  - Access tracking: GenerateServiceLastAccessedDetails, GetServiceLastAccessedDetails
- **CloudTrail Read**: Query event history for activity tracking
  - LookupEvents (read-only access to CloudTrail logs)

**Security Principle**: Least privilege - read-only IAM access, no modification capabilities

## Data Flow

### Input Stage
   - `targets`: Array of entities to audit (required)
     - Each target has `type` ("role", "policy", or "user") and `name` (entity name or ARN)
   - `include_last_access`: Include IAM Access Advisor data (default: true)
   - `include_cloudtrail_usage`: Include CloudTrail activity tracking (default: true)
   - `cloudtrail_lookup_days`: Days to look back in CloudTrail (default: 90, max: 90)
   - `policy_arn`: Specific policy ARN (optional)

### Processing Stage
2. Lambda function retrieves IAM configuration:
   - Role trust policies and permissions
   - Attached managed policies (AWS and custom)
   - Inline policies
   - Policy document versions
   - IAM user permissions (if user type specified)

3. Data enrichment and classification:
   - Parse policy JSON structures
   - Classify AWS services and actions
   - Determine access types (Read/Write/List/Delete/Admin)
   - Track CloudTrail events for role assumptions and user activity
   - Query IAM Access Advisor for service usage patterns
   - Identify security risks and wildcards
   - Extract resource-level constraints

### Output Stage
4. Generate comprehensive Excel report with multiple sheets
   - Roles & Users: 5 sheets (Detailed Permissions, Service Summary, Risk Findings, Last Access, CloudTrail Activity)
   - Policies: 3 sheets (Detailed Permissions, Service Summary, Risk Findings)
5. Upload report to S3 with timestamp-based naming
6. Return success response with S3 location

## Supported Entity Types

### 1. IAM Roles
- Analyzes all attached managed policies
- Parses inline policies
- Tracks role assumption events via CloudTrail
- Reports on last access per service
- Generates 5-sheet Excel report

### 2. IAM Policies
- Supports AWS-managed and customer-managed policies
- Can be specified by name or ARN
- Analyzes permission grants and resource constraints
- Generates 3-sheet Excel report (no CloudTrail/Last Access)

### 3. IAM Users
- Analyzes all attached managed policies
- Parses inline policies
- Tracks user activity via CloudTrail
- Reports on last access per service
- Generates 5-sheet Excel report

## Cost Model

**Near-Zero Cost Architecture**:
- No API Gateway (no per-request charges)
- No databases (no RDS/DynamoDB costs)
- No running servers (pure serverless)
- Pay only for Lambda execution time and S3 storage
- Estimated cost: < $1/month for typical usage patterns
