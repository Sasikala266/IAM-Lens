# IAM Audit Utility - Features Documentation

## Overview

The IAM Audit Utility provides comprehensive IAM role and policy analysis through automated scanning and reporting. It answers critical security audit questions:

- **Which resources** can access **what services**?
- **What actions** can be performed?
- **What resource-level** permissions exist?
- **What security risks** are present?
- **When** were permissions last used?

## Excel Report Structure

The utility generates a comprehensive Excel workbook with **5 sheets**, each serving a specific audit purpose:

### Sheet 1: Role Details

**Purpose**: High-level overview of the IAM role configuration

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Role Name | IAM role identifier | `MyApplicationRole` |
| Role ARN | Full Amazon Resource Name | `arn:aws:iam::123456789012:role/MyApplicationRole` |
| Creation Date | When role was created | `2024-01-15 10:30:00` |
| Last Used | Most recent role assumption | `2024-03-20 14:22:35` |
| Trust Policy | Who can assume the role | `lambda.amazonaws.com` |
| Description | Role description | `Application backend role` |
| Tags | Associated metadata | `Environment: Production` |
| Max Session Duration | Maximum session length | `3600 seconds` |

**Use Case**: Quick role identification and basic configuration review

---

### Sheet 2: Detailed Permissions

**Purpose**: Granular breakdown of all permissions granted to the role

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Policy Name | Name of the policy | `AmazonS3ReadOnlyAccess` |
| Policy Type | Managed, Inline, or AWS Managed | `AWS Managed` |
| Policy ARN | Full policy ARN (if managed) | `arn:aws:iam::aws:policy/...` |
| Service | AWS service name | `Amazon S3` |
| Action | Specific IAM action | `s3:GetObject` |
| Resource | Resource constraint | `arn:aws:s3:::my-bucket/*` |
| Effect | Allow or Deny | `Allow` |
| Condition | Conditional constraints | `IpAddress: 10.0.0.0/8` |
| Access Type | Classification of action | `Read` |

**Features**:
- One row per permission statement
- Fully expanded policy documents
- Includes both attached and inline policies
- Shows resource-level constraints
- Displays conditional access requirements

**Use Case**: Deep-dive permission analysis, compliance verification, least-privilege reviews

---

### Sheet 3: Service Summary

**Purpose**: Aggregated view of access levels per AWS service

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| AWS Service | Service name | `Amazon S3` |
| Read Access | Count of read actions | `15` |
| Write Access | Count of write actions | `8` |
| List Access | Count of list actions | `5` |
| Delete Access | Count of delete actions | `3` |
| Admin Access | Count of admin actions | `0` |
| Wildcard Actions | Has wildcard permissions | `No` |
| Total Actions | Total action count | `31` |
| Risk Level | Calculated risk score | `Medium` |

**Access Type Classifications**:

1. **Read Access**: Actions that retrieve or view data
   - Examples: `s3:GetObject`, `dynamodb:GetItem`, `ec2:DescribeInstances`

2. **Write Access**: Actions that create or modify resources
   - Examples: `s3:PutObject`, `dynamodb:PutItem`, `ec2:RunInstances`

3. **List Access**: Actions that enumerate resources
   - Examples: `s3:ListBucket`, `iam:ListUsers`, `ec2:DescribeVolumes`

4. **Delete Access**: Actions that remove resources
   - Examples: `s3:DeleteObject`, `ec2:TerminateInstances`, `iam:DeleteUser`

5. **Admin Access**: Full administrative permissions
   - Examples: `*:*`, `s3:*`, `iam:*`

**Use Case**: Quick service-level access assessment, identifying over-privileged roles

---

### Sheet 4: Risk Findings

**Purpose**: Security risk identification and compliance flagging

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Risk Type | Category of risk | `Wildcard Resource` |
| Severity | Impact level | `High` |
| Service | Affected AWS service | `IAM` |
| Action | Risky action pattern | `iam:*` |
| Resource | Resource specification | `*` |
| Description | Risk explanation | `Full IAM admin access granted` |
| Recommendation | Remediation guidance | `Restrict to specific IAM actions` |
| Policy Name | Source policy | `AdminPolicy` |

**Risk Categories**:

#### 1. Wildcard Permissions
- **Detection**: Actions or resources using `*`
- **Risk**: Over-broad access, violates least privilege
- **Example**: `s3:*` on `*` resources
- **Severity**: High to Critical

#### 2. Write-Level Access
- **Detection**: Write actions on sensitive services
- **Risk**: Data modification, configuration changes
- **Example**: `iam:PutUserPolicy`
- **Severity**: Medium to High

#### 3. Delete-Level Access
- **Detection**: Delete actions on critical resources
- **Risk**: Data loss, service disruption
- **Example**: `s3:DeleteBucket`, `rds:DeleteDBInstance`
- **Severity**: High

#### 4. PassRole Permissions
- **Detection**: `iam:PassRole` action present
- **Risk**: Privilege escalation vector
- **Example**: `iam:PassRole` with wildcard resources
- **Severity**: Critical

#### 5. Sensitive Service Access
- **Detection**: Access to security-critical services
- **Services**: IAM, KMS, Secrets Manager, STS, Organizations
- **Risk**: Security control bypass, credential exposure
- **Severity**: High to Critical

#### 6. Cross-Account Access
- **Detection**: Resource ARNs from different accounts
- **Risk**: Data exfiltration, unauthorized access
- **Severity**: Medium to High

#### 7. No Resource Constraints
- **Detection**: `Resource: "*"` in policy statements
- **Risk**: Access to all resources in service
- **Severity**: Medium to High

**Use Case**: Security audits, compliance checks, vulnerability identification

---

### Sheet 5: Last Access

**Purpose**: Track actual usage of granted permissions

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Service Name | AWS service | `Amazon S3` |
| Service Namespace | IAM namespace | `s3` |
| Last Accessed | Timestamp of last use | `2024-03-15 09:45:12` |
| Days Since Access | Time elapsed | `5 days` |
| Region | Where service was accessed | `us-east-1` |
| Total Granted Actions | Actions available | `25` |
| Status | Usage status | `Recently Used / Never Used` |

**Data Source**: AWS IAM Access Advisor API

**Features**:
- Service-level last access tracking
- Identifies unused permissions (candidates for removal)
- Helps enforce least privilege
- Tracks regional access patterns

**Use Case**: 
- Identify unused permissions for removal
- Validate least privilege implementation
- Support for periodic access reviews
- Compliance with security best practices

---

## Audit Capabilities

### 1. Policy Source Tracking
The utility tracks permissions from multiple sources:
- **AWS Managed Policies**: Pre-built AWS policies
- **Customer Managed Policies**: Organization-created policies
- **Inline Policies**: Policies directly embedded in roles

### 2. Multi-Version Support
- Analyzes default (active) policy versions
- Identifies policy version metadata
- Tracks policy changes over time

### 3. Condition Analysis
Evaluates IAM policy conditions:
- IP address restrictions
- Time-based constraints
- MFA requirements
- Source VPC/VPC Endpoint constraints
- Tag-based conditions

### 4. Trust Policy Analysis
Reviews who can assume the role:
- Service principals (AWS services)
- Account principals (cross-account access)
- Federated users (SSO/SAML)
- Specific IAM users or roles

## Benefits Over Manual Auditing

| Manual Approach | IAM Audit Utility |
|-----------------|-------------------|
| Multiple AWS consoles | Single automated report |
| Hours of manual work | Minutes of execution |
| Prone to human error | Consistent and accurate |
| Point-in-time snapshot | Repeatable on-demand |
| Difficult to compare | Excel format for analysis |
| No aggregation | Automatic categorization |
| Hard to identify risks | Built-in risk detection |

## Report Output Format

- **File Format**: Excel (.xlsx)
- **File Naming**: `iam-audit-{role-name}-{timestamp}.xlsx`
- **Storage**: Amazon S3 bucket with encryption
- **Retention**: Configurable via S3 lifecycle policies
- **Accessibility**: Download via AWS Console or AWS CLI
