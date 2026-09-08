# 📚 IAM Lens - Documentation Hub

### Complete Guide to Automated IAM Auditing

/IAM-Lens-Documentation/

---

## Table of Contents

- [Overview](#-overview)
- [Documentation Guides](#-documentation-guides)
- [Quick Navigation](#-quick-navigation)
- [Getting Help](#-getting-help)

---

## 🌟 Overview

The **IAM Lens** is a serverless AWS solution that automates IAM role and policy auditing. It generates comprehensive Excel reports with detailed permissions, service access, security risks, and usage analytics.

### What This Documentation Covers

This documentation provides everything you need to:
- ✅ Understand the problem the utility solves
- ✅ Deploy the infrastructure in your AWS account
- ✅ Run IAM audits for roles and policies
- ✅ Interpret audit reports and findings
- ✅ Implement security best practices
- ✅ Troubleshoot common issues

---

## 📖 Documentation Guides

### 🚀 [Getting Started](getting-started.md)
**Start here if you're new to the IAM Lens**

Learn how to:
- Install prerequisites (Terraform, AWS CLI)
- Configure AWS credentials
- Deploy the infrastructure
- Run your first IAM audit
- Download and review reports

**Time to complete:** 15-20 minutes

---

### 📊 [Features](features.md)
**Understand what the utility can do**

Explore:
- Detailed report structure (5 Excel worksheets)
- Permission classification (Read/Write/Delete/Admin)
- Security risk detection
- Last access tracking
- Service-level access summary
- Policy source tracking

**Best for:** Understanding report outputs and capabilities

---

### 🏗️ [Architecture](architecture.md)
**Learn how the system works**

Understand:
- Serverless architecture design
- Component details (Lambda, S3, IAM)
- Data flow and processing stages
- Security model
- Cost model
- Technical specifications

**Best for:** Technical teams, security architects, DevOps engineers

---

### 📖 [Usage Guide](usage-guide.md)
**Master advanced usage scenarios**

Discover:
- All input format options
- Multiple invocation methods (CLI, Console, SDK)
- Scheduling automated audits
- Batch auditing multiple roles
- CI/CD integration examples
- Troubleshooting solutions
- Best practices

**Best for:** Daily operations and advanced use cases

---

### 🎥 [Video Tutorials](videos.md)
**Watch step-by-step guides**

View:
- Deployment walkthrough
- Running audits demo
- Report interpretation
- Advanced features
- Troubleshooting tips

> 🚧 **Note:** Video content is currently in production. Check back soon!

**Best for:** Visual learners

---

## 🗺️ Quick Navigation

### By Task

| Task | Documentation |
|------|---------------|
| 🆕 First time setup | [Getting Started](getting-started.md#prerequisites) |
| 🏗️ Deploy infrastructure | [Getting Started - Deployment](getting-started.md#-deployment) |
| ▶️ Run an audit | [Getting Started - Basic Usage](getting-started.md#-basic-usage) |
| 📊 Understand reports | [Features - Report Structure](features.md#excel-report-structure) |
| 🚨 Review security risks | [Features - Risk Findings](features.md#sheet-4-risk-findings) |
| ⏰ Schedule audits | [Usage Guide - Advanced Usage](usage-guide.md#method-5-scheduled-execution-eventbridge) |
| 🔄 Batch audit roles | [Usage Guide - Advanced Usage](usage-guide.md#1-audit-all-roles-in-account) |
| 🛠️ Fix issues | [Usage Guide - Troubleshooting](usage-guide.md#-troubleshooting) |
| 🏗️ Understand architecture | [Architecture](architecture.md) |
| 🎥 Watch videos | [Videos](videos.md) |

### By Audience

**Cloud Security Engineers:**
1. [Getting Started](getting-started.md) → Deploy and run first audit
2. [Features](features.md) → Understand report structure
3. [Usage Guide](usage-guide.md) → Schedule regular audits

**DevOps Teams:**
1. [Architecture](architecture.md) → Understand system design
2. [Getting Started](getting-started.md) → Terraform deployment
3. [Usage Guide](usage-guide.md) → CI/CD integration

**Compliance Teams:**
1. [Features](features.md) → Report capabilities
2. [Getting Started](getting-started.md) → Generate first report
3. [Usage Guide](usage-guide.md) → Schedule automated audits

**Management:**
1. [Main README](../README.md) → High-level overview
2. [Features](features.md) → Benefits and capabilities
3. [Architecture](architecture.md) → Cost model

---

## 💡 Getting Help

### Common Questions

**Q: How do I get started?**  
A: Follow the [Getting Started Guide](getting-started.md) - it takes 15-20 minutes to deploy and run your first audit.

**Q: What does the report contain?**  
A: See [Features - Report Structure](features.md#excel-report-structure) for a detailed breakdown of all 5 worksheets.

**Q: How much does it cost?**  
A: Typically less than $1/month. See [Architecture - Cost Model](architecture.md#cost-model) for details.

**Q: Is it secure?**  
A: Yes! The Lambda role has read-only IAM permissions and cannot modify anything. See [Architecture - Security](architecture.md#3-iam-role--permissions).

**Q: Something isn't working!**  
A: Check the [Troubleshooting Guide](usage-guide.md#-troubleshooting) for solutions to common issues.

**Q: Can I schedule automated audits?**  
A: Yes! See [Scheduled Execution](usage-guide.md#method-5-scheduled-execution-eventbridge) in the Usage Guide.

**Q: Can I audit multiple roles at once?**  
A: Yes! See [Batch Auditing](usage-guide.md#1-audit-all-roles-in-account) in the Usage Guide.

---

## 📚 Additional Resources

### Quick Reference

- **Prerequisites**: [Getting Started - Prerequisites](getting-started.md#-prerequisites)
- **Input Formats**: [Usage Guide - Input Formats](usage-guide.md#-input-formats)
- **Report Sheets**: [Features - Excel Report Structure](features.md#excel-report-structure)
- **Best Practices**: [Usage Guide - Best Practices](usage-guide.md#-best-practices)
- **Glossary**: [Main README - Glossary](../README.md#-glossary)

---

<div align="center">

**Ready to get started?** → [Getting Started Guide](getting-started.md)

[⬆ Back to Top](#-iam-lens---documentation-hub)

</div>
