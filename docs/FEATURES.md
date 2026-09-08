# IAM Audit Utility - Features Documentation

## Overview

The IAM Audit Utility provides comprehensive IAM role, policy, and user analysis through automated scanning and reporting. It answers critical security audit questions:

- **Which resources** can access **what services**?
- **What actions** can be performed?
- **What resource-level** permissions exist?
- **What security risks** are present?
- **When** were permissions last used?
- **Who** is actively using specific permissions?

## Excel Report Structure

The utility generates comprehensive Excel workbooks with multiple sheets based on the target type:

### Report Types

#### 1. Role Reports (5 Sheets)

For IAM roles, the report includes:
- **Detailed Permissions**: Granular permission breakdown
- **Service Summary**: Aggregated service-level access
- **Risk Findings**: Security risk identification
- **Last Access**: Service usage tracking
- **Role Usage CloudTrail**: Role assumption events

#### 2. Policy Reports (3 Sheets)

For standalone managed policies, the report includes:
- **Detailed Permissions**: Granular permission breakdown
- **Service Summary**: Aggregated service-level access
- **Risk Findings**: Security risk identification

#### 3. User Reports (5 Sheets)

For IAM users, the report includes:
- **Detailed Permissions**: Granular permission breakdown
- **Service Summary**: Aggregated service-level access
- **Risk Findings**: Security risk identification
- **Last Access**: Service usage tracking
- **User Activity CloudTrail**: User API activity and sign-in events

---

## Sheet Details

### Sheet 1: Detailed Permissions

**Purpose**: Granular breakdown of all permissions granted to the role, policy, or user

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Input Type | Type of target | `Role`, `Policy`, or `User` |
| Role Name | IAM role identifier | `MyApplicationRole` |
| User Name | IAM user identifier | `john.doe` |
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
### Sheet 2: Service Summary

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

### Sheet 3: Risk Findings

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

### Sheet 4: Last Access (Roles and Users Only)

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
**Applies To**: IAM Roles and IAM Users

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

### Sheet 5a: Role Usage CloudTrail (Roles Only)

**Purpose**: Track role assumption events and session details

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Event Time | When role was assumed | `2024-03-20 14:22:35` |
| Event Name | Type of assume role event | `AssumeRole` |
| Who Assumed Role | Principal that assumed role | `arn:aws:iam::123456789012:user/admin` |
| Source Identity | Source identity if set | `admin@example.com` |
| Role Session Name | Session identifier | `admin-session-123` |
| Source IP Address | Origin IP | `10.0.1.100` |
| User Agent | Client used | `aws-cli/2.0` |
| MFA Authenticated | MFA status | `true` |
| Error Code | Any errors | `AccessDenied` |

**Data Source**: AWS CloudTrail  
**Events Tracked**: AssumeRole, AssumeRoleWithSAML, AssumeRoleWithWebIdentity

---

### Sheet 5b: User Activity CloudTrail (Users Only)

**Purpose**: Track user API activity and authentication events

**Columns**:
| Column | Description | Example |
|--------|-------------|---------|
| Event Time | When action occurred | `2024-03-20 14:22:35` |
| Event Name | API action performed | `GetObject` |
| Event Source | AWS service accessed | `s3.amazonaws.com` |
| Source IP Address | Origin IP | `10.0.1.100` |
| User Agent | Client used | `aws-cli/2.0` |
| MFA Authenticated | MFA status | `true` |
| Error Code | Any errors | `AccessDenied` |

**Data Source**: AWS CloudTrail  
**Events Tracked**: All API calls made by the user

---

## Audit Capabilities

### 1. Policy Source Tracking
The utility tracks permissions from multiple sources:
- **AWS Managed Policies**: Pre-built AWS policies
- **Customer Managed Policies**: Organization-created policies
- **Inline Policies**: Policies directly embedded in roles
- **User Policies**: Both attached and inline policies for IAM users

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

### 5. User Activity Tracking
- CloudTrail events for IAM users
- Sign-in events and API usage
- Authentication details including MFA status
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

- **File Naming**: `{target-name}_{account-id}_{timestamp}.xlsx`
- **Storage**: Amazon S3 bucket with encryption
- **Retention**: Configurable via S3 lifecycle policies
- **Accessibility**: Download via AWS Console or AWS CLI
