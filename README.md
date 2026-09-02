<div align="center">

# 🔍 IAM Audit Utility

### Automated IAM Role & Policy Auditing for AWS

![AWS](https://img.shields.io/badge/AWS-FF9900?style=for-the-badge&logo=amazon-aws&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)
![Serverless](https://img.shields.io/badge/Serverless-FD5750?style=for-the-badge&logo=serverless&logoColor=white)

**[Getting Started](docs/getting-started.md)** • **[Features](docs/features.md)** • **[Architecture](docs/architecture.md)** • **[Usage Guide](docs/usage-guide.md)** • **[Videos](docs/videos.md)**

</div>

---

## 📋 Table of Contents

- [🎯 The Problem](#-the-problem)
- [💡 The Solution](#-the-solution)
- [🏗️ Architecture Overview](#️-architecture-overview)
- [📊 What You Get](#-what-you-get)
- [🚀 Quick Start](#-quick-start)
- [📸 Sample Output](#-sample-output)
- [🎥 Video Tutorials](#-video-tutorials)
- [📚 Documentation](#-documentation)
- [💰 Cost](#-cost)
- [🔒 Security](#-security)
- [📖 Glossary](#-glossary)

---

## 🎯 The Problem

### Manual IAM Auditing is Time-Consuming and Error-Prone

AWS Identity and Access Management (IAM) is crucial for cloud security, but auditing IAM roles and policies manually is challenging:

**⏰ Time-Intensive Process**
- Reviewing a single IAM role requires navigating multiple AWS console pages
- Understanding what permissions are granted involves reading complex JSON policy documents
- Checking when permissions were last used requires accessing IAM Access Advisor
- Analyzing security risks demands expertise in AWS security best practices

**🔍 Multiple Tools Required**
- **IAM Console**: View roles and attached policies
- **Policy Simulator**: Test policy effects
- **CloudTrail**: Track API usage
- **Access Advisor**: Check last accessed services
- **Access Analyzer**: Identify security findings

**❌ Common Challenges**
- **Lack of Visibility**: Hard to see all permissions in one place
- **Complex Policies**: JSON policy documents are difficult to parse
- **Compliance Gaps**: Manual audits miss security risks
- **No Historical Records**: Point-in-time snapshots with no audit trail
- **Resource Constraints**: Security teams overwhelmed with manual reviews

**🌐 Real-World Scenario**

Imagine you're a cloud security engineer asked to:
> *"Audit our Lambda execution role to ensure it follows least-privilege principles and identify any security risks."*

You would need to:
1. Open IAM Console → Find the role
2. Review trust policy → Understand who can assume it
3. Check all attached managed policies → AWS and custom
4. Review inline policies → Embedded permissions
5. Parse JSON documents → Identify specific permissions
6. Classify actions → Read, write, delete, admin access
7. Check Access Advisor → When were services last used
8. Identify risks → Wildcards, overly permissive actions
9. Document findings → Create report for stakeholders
10. Repeat for every role in your environment

**This process can take 30-60 minutes per role!**

---

## 💡 The Solution

### Automated, Comprehensive IAM Auditing in Minutes

**IAM Audit Utility** is a serverless AWS solution that automates the entire IAM auditing process, generating comprehensive Excel reports with actionable insights.

#### ✨ Key Benefits

| Manual Approach | IAM Audit Utility |
|----------------|-------------------|
| ⏱️ **30-60 minutes** per role | ⚡ **2-3 minutes** per role |
| 🖱️ Multiple console tabs | 📊 Single Excel report |
| 🧠 Requires deep IAM expertise | 📖 Easy-to-read categorized data |
| ❌ Prone to human error | ✅ Consistent and accurate |
| 📝 Manual documentation | 🤖 Automated report generation |
| 🔍 Hard to find security risks | 🚨 Built-in risk detection |
| 💾 No historical tracking | 📈 S3-stored audit history |

#### 🎯 What It Does

1. **Extracts IAM Data** 
   - Retrieves role details, policies, and permissions via AWS APIs
   - Fetches both managed policies (AWS/custom) and inline policies
   - Gathers last access information from IAM Access Advisor

2. **Analyzes Permissions**
   - Parses complex JSON policy documents
   - Classifies actions by type: Read, Write, List, Delete, Admin
   - Identifies AWS services that can be accessed
   - Detects resource-level constraints and conditions

3. **Identifies Security Risks**
   - Wildcard permissions (`*:*`, `s3:*`, etc.)
   - Overly permissive resource access (`Resource: "*"`)
   - Sensitive service access (IAM, KMS, Secrets Manager)
   - Privilege escalation vectors (`iam:PassRole`)
   - Unused permissions (never accessed in X days)

4. **Generates Excel Reports**
   - 5 detailed worksheets covering different aspects
   - Professional formatting with color-coded risk levels
   - Ready to share with stakeholders and compliance teams
   - Stored in S3 with version history

#### 🌟 Who Benefits

- **Cloud Security Engineers**: Conduct faster, more thorough IAM audits
- **Compliance Teams**: Generate audit reports for regulatory requirements
- **DevOps Teams**: Validate least-privilege principles in automation
- **Security Auditors**: Assess IAM configurations across multiple accounts
- **Platform Engineers**: Monitor and review IAM roles at scale

---

## 🏗️ Architecture Overview

### Serverless, Simple, and Secure

```
┌──────────────────────────────────────────────────────────────┐
│                    IAM Audit Utility Flow                     │
└──────────────────────────────────────────────────────────────┘

  👤 User / ⏰ Scheduler
         │
         │ 1️⃣ Invoke with role name
         │    {"role_name": "MyAppRole"}
         ▼
  ┌─────────────────────────────────────────┐
  │      🐍 AWS Lambda Function             │
  │      (Python 3.11 - Serverless)         │
  │                                          │
  │  ┌────────────────────────────────────┐ │
  │  │ 📥 Fetch IAM Data (boto3)         │ │
  │  │  • Role details & trust policy    │ │
  │  │  • Managed policies (AWS/Custom)  │ │
  │  │  • Inline policies                │ │
  │  │  • Last access information        │ │
  │  └────────────────────────────────────┘ │
  │             │                            │
  │             ▼                            │
  │  ┌────────────────────────────────────┐ │
  │  │ 🔍 Analyze & Classify              │ │
  │  │  • Parse policy JSON               │ │
  │  │  • Classify actions & services     │ │
  │  │  • Detect security risks           │ │
  │  │  • Identify unused permissions     │ │
  │  └────────────────────────────────────┘ │
  │             │                            │
  │             ▼                            │
  │  ┌────────────────────────────────────┐ │
  │  │ 📊 Generate Excel Report           │ │
  │  │  • 5 worksheets                    │ │
  │  │  • Formatted & color-coded         │ │
  │  └────────────────────────────────────┘ │
  └───────────────┬────────────────────────┘
                  │
                  │ 2️⃣ Upload report
                  ▼
          ┌───────────────────┐
          │  🗄️ Amazon S3     │
          │  Audit Reports    │
          │  ┌─────────────┐  │
          │  │ role1.xlsx  │  │
          │  │ role2.xlsx  │  │
          │  └─────────────┘  │
          └───────────────────┘
                  │
                  │ 3️⃣ Download & review
                  ▼
            👤 Security Team
```

### 🔧 Components

- **AWS Lambda**: Serverless compute (Python 3.11, 512MB RAM, 5-min timeout)
- **Amazon S3**: Secure storage for generated reports (encrypted, versioned)
- **IAM Role**: Read-only permissions to query IAM resources
- **boto3 SDK**: AWS API interactions
- **openpyxl**: Excel file generation

> 💡 **No servers to manage, no databases to maintain, no APIs to expose**

For detailed architecture documentation, see [Architecture Guide](docs/architecture.md).

---

## 📊 What You Get

### Comprehensive Excel Report with 5 Worksheets

#### 📄 **Sheet 1: Role Details**
High-level role information: ARN, creation date, trust policy, last used, tags

#### 🔐 **Sheet 2: Detailed Permissions**
Every permission broken down:
- Policy name and type (AWS Managed / Custom / Inline)
- AWS service and action (e.g., `s3:GetObject`)
- Resource constraints
- Conditions (IP restrictions, MFA, etc.)
- Access type classification (Read/Write/Delete/Admin)

#### 📈 **Sheet 3: Service Summary**
Aggregated view per AWS service:
- Count of Read/Write/List/Delete/Admin actions
- Wildcard detection
- Risk level assessment

#### 🚨 **Sheet 4: Risk Findings**
Security risks and compliance issues:
- Wildcard permissions (`*:*`, `s3:*`)
- Overly permissive resources (`Resource: "*"`)
- Privilege escalation vectors (`iam:PassRole`)
- Sensitive service access (IAM, KMS, Secrets Manager)
- Severity ratings (Low/Medium/High/Critical)
- Remediation recommendations

#### ⏰ **Sheet 5: Last Access**
Usage tracking:
- When each service was last accessed
- Days since last use
- Identifies unused permissions (removal candidates)

For detailed feature documentation, see [Features Guide](docs/features.md).

---

## 🚀 Quick Start

### 3 Steps to Your First Audit

**1️⃣ Deploy the Infrastructure**
```bash
git clone <repository-url>
cd iam-audit-utility
terraform init
terraform apply
```

**2️⃣ Run an Audit**
```bash
aws lambda invoke \
  --function-name iam-scanner-lambda \
  --payload '{"role_name": "MyApplicationRole"}' \
  output.json
```

**3️⃣ Download the Report**
```bash
aws s3 ls s3://audit-reports-bucket/iam-audit-reports/
aws s3 cp s3://audit-reports-bucket/iam-audit-reports/MyApplicationRole-*.xlsx ./
```

**That's it!** Open the Excel file and review your audit.

📖 For detailed instructions, see [Getting Started Guide](docs/getting-started.md).

---

## 📸 Sample Output

### Example: Auditing a Lambda Execution Role

**Input:**
```json
{
  "role_name": "lambda-execution-role"
}
```

**Output Report Includes:**
- ✅ Role has access to **3 AWS services**: S3, DynamoDB, CloudWatch Logs
- ✅ Total of **47 permissions** granted across managed and inline policies
- ⚠️ **2 Medium-risk findings**: Wildcard S3 access, no resource-level constraints
- ⚠️ **1 unused service**: DynamoDB (not accessed in 90 days)
- ℹ️ **Recommendation**: Remove DynamoDB permissions, add resource constraints to S3

**Report Preview:**
```
Sheet: Risk Findings
┌─────────────────────┬──────────┬─────────┬────────────────────────────────┐
│ Risk Type           │ Severity │ Service │ Description                     │
├─────────────────────┼──────────┼─────────┼────────────────────────────────┤
│ Wildcard Resource   │ Medium   │ S3      │ Access to all S3 buckets       │
│ Unused Permissions  │ Medium   │ DynamoDB│ Not accessed in 90 days        │
└─────────────────────┴──────────┴─────────┴────────────────────────────────┘
```

---

## 🎥 Video Tutorials

Step-by-step video guides for deploying and using the IAM Audit Utility.

👉 [Watch Video Tutorials](docs/videos.md)

---

## 📚 Documentation

### Core Documentation

- **[Getting Started](docs/getting-started.md)** - Prerequisites, deployment, first audit
- **[Features](docs/features.md)** - Detailed report structure and capabilities
- **[Architecture](docs/architecture.md)** - System design and component details
- **[Usage Guide](docs/usage-guide.md)** - Advanced usage, troubleshooting, best practices
- **[Videos](docs/videos.md)** - Video tutorials and demos

### Quick Links

- [Prerequisites](docs/getting-started.md#prerequisites)
- [Deployment Steps](docs/getting-started.md#deployment)
- [Input Formats](docs/usage-guide.md#input-formats)
- [Troubleshooting](docs/usage-guide.md#troubleshooting)
- [Best Practices](docs/usage-guide.md#best-practices)

---

## 💰 Cost

### Near-Zero Cost Architecture

This solution is designed to be extremely cost-effective:

| Component | Pricing | Estimated Monthly Cost |
|-----------|---------|----------------------|
| AWS Lambda | $0.20 per 1M requests + compute time | **< $0.50** |
| Amazon S3 | $0.023 per GB storage | **< $0.25** |
| CloudWatch Logs | $0.50 per GB ingested | **< $0.10** |
| **Total** | - | **< $1.00/month** |

**Assumptions**: 100 audit runs per month, 10 MB per report, minimal logging

> 💡 **No API Gateway, no databases, no running servers** = minimal AWS costs

---

## 🔒 Security

### Built with Security Best Practices

- ✅ **Least Privilege**: Lambda role has read-only IAM access
- ✅ **No Modification**: Cannot change IAM configurations
- ✅ **Encryption**: S3 reports encrypted at rest (AES-256)
- ✅ **Private Access**: S3 bucket blocks public access
- ✅ **Audit Trail**: CloudWatch Logs capture all executions
- ✅ **Version Control**: S3 versioning tracks report history

---

## 📖 Glossary

### Key Terms

**IAM (Identity and Access Management)**
AWS service that controls who can access what resources in your AWS account.

**IAM Role**
An AWS identity with specific permissions that can be assumed by users, applications, or services.

**IAM Policy**
A JSON document that defines permissions (what actions are allowed/denied on which resources).

**Managed Policy**
A standalone policy that can be attached to multiple roles/users. Can be AWS-managed or customer-managed.

**Inline Policy**
A policy embedded directly within a single role/user (1:1 relationship).

**Trust Policy**
Defines who or what can assume an IAM role (e.g., Lambda service, EC2 instances, another AWS account).

**Action**
A specific operation in AWS (e.g., `s3:GetObject`, `ec2:DescribeInstances`, `iam:CreateUser`).

**Resource**
The AWS entity that an action is performed on (e.g., S3 bucket, EC2 instance, IAM user).

**Principal**
The entity (user, role, service) that is allowed or denied access in a policy.

**Access Advisor**
AWS IAM feature that shows when a role/user last accessed a service.

**Least Privilege**
Security principle: grant only the minimum permissions needed to perform a task.

**Wildcard Permission**
Using `*` in policies to grant broad access (e.g., `s3:*` allows all S3 actions).

**PassRole**
IAM action (`iam:PassRole`) that allows giving a role to an AWS service. Can be a privilege escalation vector.

**Serverless**
Architecture pattern where you run code without managing servers (AWS Lambda is serverless compute).

**boto3**
The AWS SDK (Software Development Kit) for Python, used to interact with AWS services programmatically.

**CloudWatch Logs**
AWS service for storing and analyzing log data from applications and AWS services.

**S3 (Simple Storage Service)**
AWS object storage service for storing files (like our Excel audit reports).

**ARN (Amazon Resource Name)**
Unique identifier for AWS resources (e.g., `arn:aws:iam::123456789012:role/MyRole`).

**Terraform**
Infrastructure-as-code tool for provisioning AWS resources using declarative configuration files.

---

<div align="center">

**Made with ❤️ for AWS Security Teams**

[⬆ Back to Top](#-iam-audit-utility)

</div>
