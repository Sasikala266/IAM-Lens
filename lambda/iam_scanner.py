import boto3
import json
import re
import time
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import unquote
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

iam = boto3.client("iam")
s3 = boto3.client("s3")
sts = boto3.client("sts")
cloudtrail = boto3.client("cloudtrail")

def lambda_handler(event, context):
    output_bucket = os.environ["S3_BUCKET_NAME"]
    output_prefix = os.environ.get("REPORT_PREFIX","iam-audit-reports")
    include_last_access = event.get("include_last_access", True)
    include_cloudtrail_usage = event.get("include_cloudtrail_usage", True)
    cloudtrail_lookup_days = int(event.get("cloudtrail_lookup_days", 90))
    cloudtrail_lookup_days = min(cloudtrail_lookup_days, 90)
    cloudtrail_max_pages = int(event.get("cloudtrail_max_pages", 5))
    account_id = sts.get_caller_identity()["Account"]
    generated_reports = []
    
    # Parse input format - support both new structured format and legacy format
    targets_to_process = []
    
    # Check for new structured format
    if "targets" in event:
        targets = event.get("targets", [])
        for target in targets:
            target_type = target.get("type", "").lower()
            if target_type == "role":
                targets_to_process.append({
                    "type": "role",
                    "name": target.get("name", "")
                })
            elif target_type == "policy":
                targets_to_process.append({
                    "type": "policy",
                    "name": target.get("name", "")
                })
            elif target_type == "user":
                user_name = target.get("name", "").strip()
                if not user_name:
                    print(f"Warning: Skipping user target with empty name: {target}")
                else:
                    targets_to_process.append({
                        "type": "user",
                        "name": user_name
                    })
    elif "role_names" in event:
        role_names = event.get("role_names", [])
        for role_name in role_names:
            targets_to_process.append({
                "type": "role",
                "name": role_name
            })
    
    if not targets_to_process:
        return {
            "status": "failed",
            "message": "Please provide at least one IAM Role/Policy/User"
        }
    
    # Process each target
    for target in targets_to_process:
        if target["type"] == "role":
            role_name = target["name"]
            process_role(role_name, account_id, output_bucket, output_prefix, 
                        include_last_access, include_cloudtrail_usage, 
                        cloudtrail_lookup_days, cloudtrail_max_pages, generated_reports)
        elif target["type"] == "policy":
            policy_identifier = target["name"]
            process_policy(policy_identifier, account_id, output_bucket, output_prefix, generated_reports)
        elif target["type"] == "user":
            user_name = target["name"]
            process_user(user_name, account_id, output_bucket, output_prefix, 
                        include_last_access, include_cloudtrail_usage, cloudtrail_lookup_days, cloudtrail_max_pages, generated_reports)
    
    return {
        "status": "success",
        "message": "IAM governance reports generated successfully",
        "total_targets_processed": len(generated_reports),
        "reports": generated_reports
    }

def process_role(role_name, account_id, output_bucket, output_prefix, 
                 include_last_access, include_cloudtrail_usage, 
                 cloudtrail_lookup_days, cloudtrail_max_pages, generated_reports):
    """Process a single role and generate report"""
    try:
        print(f"Processing role: {role_name}")
        role_result = audit_role(account_id, role_name)
        detailed_rows = role_result["detailed_rows"]
        risk_rows = role_result["risk_rows"]
        role_arn = role_result["role_arn"]
        service_summary_rows = build_service_summary(detailed_rows)
        if include_last_access and role_arn:
            last_access_rows = get_last_access_details(
                account_id=account_id,
                role_name=role_name,
                role_arn=role_arn
            )
        else:
            last_access_rows = [{
                "AccountId": account_id,
                "RoleName": role_name,
                "RoleArn": role_arn or "",
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": "Skipped"
            }]
        if include_cloudtrail_usage and role_arn:
            role_usage_rows = get_role_usage_from_cloudtrail(
                account_id=account_id,
                role_name=role_name,
                role_arn=role_arn,
                lookup_days=cloudtrail_lookup_days,
                max_pages=cloudtrail_max_pages
            )
        else:
            role_usage_rows = [{
                "AccountId": account_id,
                "RoleName": role_name,
                "RoleArn": role_arn or "",
                "EventTime": "",
                "EventName": "",
                "WhoAssumedRole": "",
                "SourceIdentity": "",
                "RoleSessionName": "",
                "SourceIPAddress": "",
                "UserAgent": "",
                "AwsRegion": "",
                "MFAAuthenticated": "",
                "ErrorCode": "",
                "Status": "Skipped"
            }]
        if not detailed_rows:
            detailed_rows = [{
                "AccountId": account_id,
                "InputType": "Role",
                "RoleName": role_name,
                "RoleArn": role_arn or "",
                "PolicyName": "",
                "PolicyType": "",
                "Effect": "",
                "Service": "",
                "Action": "",
                "AccessType": "",
                "Resource": "",
                "ResourceLevel": "",
                "Condition": "",
                "RiskFlag": "No permissions found or unable to parse policies"
            }]
        if not risk_rows:
            risk_rows = [{
                "AccountId": account_id,
                "RoleName": role_name,
                "PolicyName": "",
                "Finding": "No high-risk findings identified by static parser",
                "Severity": "Info",
                "Resource": "",
                "Action": ""
            }]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_role_name = sanitize_name(role_name)
        file_name = f"{safe_role_name}_{account_id}_{timestamp}.xlsx"
        local_path = f"/tmp/{file_name}"
        s3_key = f"{output_prefix.rstrip('/')}/{file_name}"
        write_excel_report_for_role(
            local_path=local_path,
            detailed_rows=detailed_rows,
            summary_rows=service_summary_rows,
            risk_rows=risk_rows,
            last_access_rows=last_access_rows,
            role_usage_rows=role_usage_rows
        )
        s3.upload_file(local_path, output_bucket, s3_key)
        generated_reports.append({
            "role_name": role_name,
            "role_arn": role_arn,
            "file_name": file_name,
            "s3_uri": f"s3://{output_bucket}/{s3_key}",
            "detailed_permission_rows": len(detailed_rows),
            "risk_rows": len(risk_rows),
            "last_access_rows": len(last_access_rows),
            "cloudtrail_usage_rows": len(role_usage_rows)
        })
        print(f"Completed report for {role_name}: s3://{output_bucket}/{s3_key}")
    except Exception as e:
        print(f"Error processing role {role_name}: {str(e)}")
        generated_reports.append({
            "role_name": role_name,
            "role_arn": "",
            "status": "failed",
            "error": str(e)
        })

def process_policy(policy_arn, account_id, output_bucket, output_prefix, generated_reports):
def process_policy(policy_identifier, account_id, output_bucket, output_prefix, generated_reports):
    try:
        # Validate policy ARN before processing
        if not policy_arn or not isinstance(policy_arn, str):
        if not policy_identifier or not isinstance(policy_identifier, str):
            print(f"Error: {error_msg}")
            generated_reports.append({
                "policy_arn": str(policy_arn),
                "policy_arn": str(policy_identifier),
                "error": error_msg
            })
            return
        
        print(f"Processing policy: {policy_identifier}")
        policy_result = audit_standalone_policy(account_id, policy_identifier)
        detailed_rows = policy_result["detailed_rows"]
        risk_rows = policy_result["risk_rows"]
        policy_name = policy_result["policy_name"]
        policy_arn = policy_result["policy_arn"]
        
        service_summary_rows = build_service_summary(detailed_rows)
        
        if not detailed_rows:
            detailed_rows = [{
                "AccountId": account_id,
                "InputType": "Policy",
                "PolicyName": policy_name,
                "PolicyArn": policy_arn,
                "RoleName": "",
                "RoleArn": "",
                "PolicyType": "Managed",
                "Effect": "",
                "Service": "",
                "Action": "",
                "AccessType": "",
                "Resource": "",
                "ResourceLevel": "",
                "Condition": "",
                "RiskFlag": "No permissions found or unable to parse policy"
            }]
        
        if not risk_rows:
            risk_rows = [{
                "AccountId": account_id,
                "PolicyName": policy_name,
                "PolicyArn": policy_arn,
                "Finding": "No high-risk findings identified by static parser",
                "Severity": "Info",
                "Resource": "",
                "Action": ""
            }]
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_policy_name = sanitize_name(policy_name)
        file_name = f"{safe_policy_name}_{account_id}_{timestamp}.xlsx"
        local_path = f"/tmp/{file_name}"
        s3_key = f"{output_prefix.rstrip('/')}/{file_name}"
        
        write_excel_report_for_policy(
            local_path=local_path,
            detailed_rows=detailed_rows,
            summary_rows=service_summary_rows,
            risk_rows=risk_rows
        )
        
        s3.upload_file(local_path, output_bucket, s3_key)
        
        generated_reports.append({
            "policy_name": policy_name,
            "policy_arn": policy_arn,
            "file_name": file_name,
            "s3_uri": f"s3://{output_bucket}/{s3_key}",
            "detailed_permission_rows": len(detailed_rows),
            "risk_rows": len(risk_rows)
        })
        print(f"Completed report for policy {policy_name}: s3://{output_bucket}/{s3_key}")
    except Exception as e:
        print(f"Error processing policy {policy_identifier}: {str(e)}")
        generated_reports.append({
            "policy_arn": policy_identifier,
            "status": "failed",
            "error": str(e)
        })

def audit_standalone_policy(account_id, policy_identifier):
    """Audit a standalone managed policy"""
    detailed_rows = []
    risk_rows = []
    policy_name = ""
    policy_arn = ""
    
    try:
        # Resolve policy identifier to ARN
        policy_arn = resolve_policy_arn(policy_identifier, account_id)
        
        policy_meta = iam.get_policy(PolicyArn=policy_arn)["Policy"]
        policy_name = policy_meta["PolicyName"]
        default_version_id = policy_meta["DefaultVersionId"]
        
        version_response = iam.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=default_version_id
        )
        
        policy_document = normalize_policy_document(
            version_response["PolicyVersion"]["Document"]
        )
        
        detailed_rows, risk_rows = parse_policy_document(
            account_id=account_id,
            input_type="Policy",
            role_name="",
            policy_arn=policy_arn,
            role_arn="",
            policy_name=policy_name,
            policy_type="Managed",
            policy_document=policy_document
        )
    except Exception as e:
        risk_rows.append({
            "AccountId": account_id,
            "PolicyName": policy_name or policy_identifier,
            "PolicyArn": policy_arn,
            "Finding": f"Unable to read policy: {str(e)}",
            "Severity": "High",
            "Resource": "",
            "Action": ""
        })
    
    return {
        "status": "success",
        "policy_name": policy_name or policy_identifier,
        "policy_arn": policy_arn or policy_identifier,
        "detailed_rows": detailed_rows,
        "risk_rows": risk_rows
    }

def resolve_policy_arn(policy_identifier, account_id):
    """
    Resolve a policy identifier (name or ARN) to a full policy ARN.
    
    Args:
        policy_identifier: Either a policy ARN or policy name
        account_id: AWS account ID
        
    Returns:
        Full policy ARN
        
    Raises:
        Exception: If policy cannot be resolved
    """
    # If already an ARN, return as-is
    if policy_identifier.startswith("arn:"):
        return policy_identifier
    
    # Otherwise, treat as policy name and try to find it
    policy_name = policy_identifier
    
    # First, try as customer-managed policy
    customer_policy_arn = f"arn:aws:iam::{account_id}:policy/{policy_name}"
    try:
        iam.get_policy(PolicyArn=customer_policy_arn)
        print(f"Resolved policy name '{policy_name}' to customer-managed ARN: {customer_policy_arn}")
        return customer_policy_arn
    except iam.exceptions.NoSuchEntityException:
        pass
    except Exception as e:
        print(f"Error checking customer-managed policy: {str(e)}")
    
    # Try as AWS-managed policy
    aws_policy_arn = f"arn:aws:iam::aws:policy/{policy_name}"
    try:
        iam.get_policy(PolicyArn=aws_policy_arn)
        print(f"Resolved policy name '{policy_name}' to AWS-managed ARN: {aws_policy_arn}")
        return aws_policy_arn
    except iam.exceptions.NoSuchEntityException:
        pass
    except Exception as e:
        print(f"Error checking AWS-managed policy: {str(e)}")
    
    # If we can't find it as customer or AWS managed, search all policies
    try:
        marker = None
        while True:
            params = {"Scope": "Local", "MaxItems": 100}
            if marker:
                params["Marker"] = marker
            response = iam.list_policies(**params)
            for policy in response.get("Policies", []):
                if policy["PolicyName"] == policy_name:
                    found_arn = policy["Arn"]
                    print(f"Found policy '{policy_name}' via list_policies: {found_arn}")
                    return found_arn
            if response.get("IsTruncated"):
                marker = response.get("Marker")
            else:
                break
    except Exception as e:
        print(f"Error searching policies: {str(e)}")
    
    # If nothing works, raise an error
    raise Exception(f"Could not find policy: '{policy_name}'. Please provide a valid policy ARN or ensure the policy exists in account {account_id}")

def process_user(user_name, account_id, output_bucket, output_prefix, 
                 include_last_access, include_cloudtrail_usage, 
                 cloudtrail_lookup_days, cloudtrail_max_pages, generated_reports):
    """Process an IAM user and create audit report"""
    try:
        print(f"Processing user: {user_name}")
        user_audit_result = audit_user(account_id, user_name)
        detailed_rows = user_audit_result["detailed_rows"]
        risk_rows = user_audit_result["risk_rows"]
        user_arn = user_audit_result["user_arn"]
        service_summary_rows = build_service_summary(detailed_rows)
        
        if include_last_access and user_arn:
            last_access_rows = get_user_last_access_info(
                account_id=account_id,
                user_name=user_name,
                user_arn=user_arn
            )
        else:
            last_access_rows = [{
                "AccountId": account_id,
                "UserName": user_name,
                "UserArn": user_arn or "",
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": "Skipped"
            }]
        
        if include_cloudtrail_usage and user_arn:
            user_activity_rows = fetch_user_cloudtrail_activity(
                account_id=account_id,
                user_name=user_name,
                user_arn=user_arn,
                lookup_days=cloudtrail_lookup_days,
                max_pages=cloudtrail_max_pages
            )
        else:
            user_activity_rows = [{
                "AccountId": account_id,
                "UserName": user_name,
                "UserArn": user_arn or "",
                "EventTime": "",
                "EventName": "",
                "EventSource": "",
                "SourceIPAddress": "",
                "UserAgent": "",
                "AwsRegion": "",
                "MFAAuthenticated": "",
                "ErrorCode": "",
                "Status": "Skipped"
            }]
        
        if not detailed_rows:
            detailed_rows = [{
                "AccountId": account_id,
                "InputType": "User",
                "UserName": user_name,
                "UserArn": user_arn or "",
                "PolicyName": "",
                "PolicyType": "",
                "Effect": "",
                "Service": "",
                "Action": "",
                "AccessType": "",
                "Resource": "",
                "ResourceLevel": "",
                "Condition": "",
                "RiskFlag": "No permissions found or unable to parse user policies"
            }]
        
        if not risk_rows:
            risk_rows = [{
                "AccountId": account_id,
                "UserName": user_name,
                "PolicyName": "",
                "Finding": "No high-risk findings identified",
                "Severity": "Info",
                "Resource": "",
                "Action": ""
            }]
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_user_name = sanitize_name(user_name)
        file_name = f"{safe_user_name}_{account_id}_{timestamp}.xlsx"
        local_path = f"/tmp/{file_name}"
        s3_key = f"{output_prefix.rstrip('/')}/{file_name}"
        
        create_user_excel_report(
            local_path=local_path,
            detailed_rows=detailed_rows,
            summary_rows=service_summary_rows,
            risk_rows=risk_rows,
            last_access_rows=last_access_rows,
            user_activity_rows=user_activity_rows
        )
        
        s3.upload_file(local_path, output_bucket, s3_key)
        
        generated_reports.append({
            "user_name": user_name,
            "user_arn": user_arn,
            "file_name": file_name,
            "s3_uri": f"s3://{output_bucket}/{s3_key}",
            "detailed_permission_rows": len(detailed_rows),
            "risk_rows": len(risk_rows),
            "last_access_rows": len(last_access_rows),
            "cloudtrail_activity_rows": len(user_activity_rows)
        })
        print(f"Completed report for user {user_name}: s3://{output_bucket}/{s3_key}")
    except Exception as e:
        print(f"Error processing user {user_name}: {str(e)}")
        generated_reports.append({
            "user_name": user_name,
            "user_arn": "",
            "status": "failed",
            "error": str(e)
        })

def audit_user(account_id, user_name):
    """Audit IAM user permissions from all policies"""
    detailed_rows = []
    risk_rows = []
    user_arn = ""
    
    try:
        user_response = iam.get_user(UserName=user_name)
        user_arn = user_response["User"]["Arn"]
    except Exception as e:
        return {
            "user_arn": "",
            "detailed_rows": [],
            "risk_rows": [{
                "AccountId": account_id,
                "UserName": user_name,
                "PolicyName": "",
                "Finding": f"Unable to retrieve user details: {str(e)}",
                "Severity": "High",
                "Resource": "",
                "Action": ""
            }]
        }
    
    attached_user_policies = fetch_attached_user_policies(user_name)
    for policy_info in attached_user_policies:
        policy_arn = policy_info["PolicyArn"]
        policy_name = policy_info["PolicyName"]
        policy_rows, policy_risks = audit_user_managed_policy(
            account_id=account_id,
            user_name=user_name,
            user_arn=user_arn,
            policy_arn=policy_arn,
            policy_name_override=policy_name
        )
        detailed_rows.extend(policy_rows)
        risk_rows.extend(policy_risks)
    
    inline_user_policy_names = fetch_inline_user_policies(user_name)
    for policy_name in inline_user_policy_names:
        try:
            policy_response = iam.get_user_policy(
                UserName=user_name,
                PolicyName=policy_name
            )
            policy_doc = normalize_policy_document(policy_response["PolicyDocument"])
            parsed_rows, parsed_risks = parse_user_policy_document(
                account_id=account_id,
                input_type="User",
                user_name=user_name,
                policy_arn="",
                user_arn=user_arn,
                policy_name=policy_name,
                policy_type="Inline",
                policy_document=policy_doc
            )
            detailed_rows.extend(parsed_rows)
            risk_rows.extend(parsed_risks)
        except Exception as e:
            risk_rows.append({
                "AccountId": account_id,
                "UserName": user_name,
                "PolicyName": policy_name,
                "Finding": f"Unable to retrieve inline policy: {str(e)}",
                "Severity": "High",
                "Resource": "",
                "Action": ""
            })
    
    return {
        "user_arn": user_arn,
        "detailed_rows": detailed_rows,
        "risk_rows": risk_rows
    }

def fetch_attached_user_policies(user_name):
    """Retrieve all managed policies attached to user"""
    all_policies = []
    marker = None
    while True:
        params = {"UserName": user_name}
        if marker:
            params["Marker"] = marker
        response = iam.list_attached_user_policies(**params)
        all_policies.extend(response.get("AttachedPolicies", []))
        if response.get("IsTruncated"):
            marker = response.get("Marker")
        else:
            break
    return all_policies

def fetch_inline_user_policies(user_name):
    """Retrieve all inline policies for user"""
    all_policy_names = []
    marker = None
    while True:
        params = {"UserName": user_name}
        if marker:
            params["Marker"] = marker
        response = iam.list_user_policies(**params)
        all_policy_names.extend(response.get("PolicyNames", []))
        if response.get("IsTruncated"):
            marker = response.get("Marker")
        else:
            break
    return all_policy_names

def audit_user_managed_policy(account_id, user_name, user_arn, policy_arn, policy_name_override=None):
    """Audit a managed policy attached to a user"""
    try:
        policy_metadata = iam.get_policy(PolicyArn=policy_arn)["Policy"]
        default_version = policy_metadata["DefaultVersionId"]
        policy_name = policy_name_override or policy_metadata["PolicyName"]
        version_data = iam.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=default_version
        )
        policy_doc = normalize_policy_document(
            version_data["PolicyVersion"]["Document"]
        )
        return parse_user_policy_document(
            account_id=account_id,
            input_type="User",
            user_name=user_name,
            policy_arn=policy_arn,
            user_arn=user_arn,
            policy_name=policy_name,
            policy_type="Managed",
            policy_document=policy_doc
        )
    except Exception as e:
        return [], [{
            "AccountId": account_id,
            "UserName": user_name,
            "PolicyName": policy_arn,
            "Finding": f"Unable to retrieve managed policy: {str(e)}",
            "Severity": "High",
            "Resource": "",
            "Action": ""
        }]

def parse_user_policy_document(
    account_id, input_type, user_name, policy_arn, user_arn,
    policy_name, policy_type, policy_document
):
    """Parse IAM policy document for user permissions"""
    rows = []
    risks = []
    statements = policy_document.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    
    for statement in statements:
        sid = statement.get("Sid", "")
        effect = statement.get("Effect", "")
        actions = statement.get("Action", [])
        not_actions = statement.get("NotAction", [])
        resources = statement.get("Resource", [])
        not_resources = statement.get("NotResource", [])
        condition = statement.get("Condition", {})
        
        actions = ensure_list(actions)
        not_actions = ensure_list(not_actions)
        resources = ensure_list(resources)
        not_resources = ensure_list(not_resources)
        
        action_items = actions if actions else [f"NOT_ACTION::{item}" for item in not_actions]
        resource_items = resources if resources else [f"NOT_RESOURCE::{item}" for item in not_resources]
        if not resource_items:
            resource_items = [""]
        
        for action in action_items:
            service, action_name = split_action(action)
            access_type = classify_access_type(service, action_name)
            full_action = f"{service}:{action_name}" if service != "Unknown" else action_name
            
            for resource in resource_items:
                resource_level = classify_resource_level(service, resource)
                risk_flag = identify_risk_flag(
                    effect=effect,
                    service=service,
                    action_name=action_name,
                    resource=resource,
                    condition=condition
                )
                
                row = {
                    "AccountId": account_id,
                    "InputType": input_type,
                    "UserName": user_name,
                    "PolicyArn": policy_arn,
                    "UserArn": user_arn,
                    "PolicyName": policy_name,
                    "PolicyType": policy_type,
                    "StatementSid": sid,
                    "Effect": effect,
                    "Service": service,
                    "Action": action_name,
                    "FullAction": full_action,
                    "AccessType": access_type,
                    "Resource": resource,
                    "ResourceLevel": resource_level,
                    "Condition": json.dumps(condition) if condition else "",
                    "RiskFlag": risk_flag
                }
                rows.append(row)
                
                if risk_flag:
                    risks.append({
                        "AccountId": account_id,
                        "UserName": user_name,
                        "PolicyName": policy_name,
                        "Finding": risk_flag,
                        "Severity": classify_risk_severity(risk_flag),
                        "Resource": resource,
                        "Action": full_action
                    })
    
    return rows, risks

def get_user_last_access_info(account_id, user_name, user_arn):
    """Get last access information for IAM user"""
    rows = []
    try:
        generate_response = iam.generate_service_last_accessed_details(
            Arn=user_arn,
            Granularity="ACTION_LEVEL"
        )
        job_id = generate_response["JobId"]
        response = None
        
        for _ in range(10):
            response = iam.get_service_last_accessed_details(JobId=job_id)
            if response.get("JobStatus") in ["COMPLETED", "FAILED"]:
                break
            time.sleep(1)
        
        if not response or response.get("JobStatus") != "COMPLETED":
            return [{
                "AccountId": account_id,
                "UserName": user_name,
                "UserArn": user_arn,
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": f"Job status: {response.get('JobStatus') if response else 'No response'}"
            }]
        
        while True:
            services = response.get("ServicesLastAccessed", [])
            for service in services:
                tracked_actions = service.get("TrackedActionsLastAccessed", [])
                if tracked_actions:
                    for tracked_action in tracked_actions:
                        rows.append({
                            "AccountId": account_id,
                            "UserName": user_name,
                            "UserArn": user_arn,
                            "ServiceName": service.get("ServiceName", ""),
                            "ServiceNamespace": service.get("ServiceNamespace", ""),
                            "ActionName": tracked_action.get("ActionName", ""),
                            "LastAuthenticated": str(tracked_action.get("LastAccessedTime", "")),
                            "LastAuthenticatedRegion": service.get("LastAuthenticatedRegion", ""),
                            "LastAuthenticatedEntity": service.get("LastAuthenticatedEntity", ""),
                            "TotalAuthenticatedEntities": service.get("TotalAuthenticatedEntities", ""),
                            "Status": "Completed"
                        })
                else:
                    rows.append({
                        "AccountId": account_id,
                        "UserName": user_name,
                        "UserArn": user_arn,
                        "ServiceName": service.get("ServiceName", ""),
                        "ServiceNamespace": service.get("ServiceNamespace", ""),
                        "ActionName": "",
                        "LastAuthenticated": str(service.get("LastAuthenticated", "")),
                        "LastAuthenticatedRegion": service.get("LastAuthenticatedRegion", ""),
                        "LastAuthenticatedEntity": service.get("LastAuthenticatedEntity", ""),
                        "TotalAuthenticatedEntities": service.get("TotalAuthenticatedEntities", ""),
                        "Status": "Completed"
                    })
            
            marker = response.get("Marker")
            if response.get("IsTruncated") and marker:
                response = iam.get_service_last_accessed_details(
                    JobId=job_id,
                    Marker=marker
                )
            else:
                break
        
        if not rows:
            rows.append({
                "AccountId": account_id,
                "UserName": user_name,
                "UserArn": user_arn,
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": "No last accessed details found"
            })
        
        return rows
    except Exception as e:
        return [{
            "AccountId": account_id,
            "UserName": user_name,
            "UserArn": user_arn,
            "ServiceName": "",
            "ServiceNamespace": "",
            "ActionName": "",
            "LastAuthenticated": "",
            "LastAuthenticatedRegion": "",
            "LastAuthenticatedEntity": "",
            "TotalAuthenticatedEntities": "",
            "Status": f"Error: {str(e)}"
        }]

def fetch_user_cloudtrail_activity(account_id, user_name, user_arn, lookup_days, max_pages):
    """Fetch user activity from CloudTrail logs"""
    rows = []
    start_time = datetime.now(timezone.utc) - timedelta(days=lookup_days)
    end_time = datetime.now(timezone.utc)
    
    next_token = None
    page_count = 0
    
    while True:
        params = {
            "LookupAttributes": [
                {
                    "AttributeKey": "Username",
                    "AttributeValue": user_name
                }
            ],
            "StartTime": start_time,
            "EndTime": end_time,
            "MaxResults": 50
        }
        if next_token:
            params["NextToken"] = next_token
        
        try:
            response = cloudtrail.lookup_events(**params)
        except Exception as e:
            rows.append({
                "AccountId": account_id,
                "UserName": user_name,
                "UserArn": user_arn,
                "EventTime": "",
                "EventName": "",
                "EventSource": "",
                "SourceIPAddress": "",
                "UserAgent": "",
                "AwsRegion": "",
                "MFAAuthenticated": "",
                "ErrorCode": "",
                "Status": f"Error reading CloudTrail: {str(e)}"
            })
            break
        
        events = response.get("Events", [])
        for event in events:
            parsed_event = parse_user_cloudtrail_event(
                account_id=account_id,
                user_name=user_name,
                user_arn=user_arn,
                event=event
            )
            if parsed_event:
                rows.append(parsed_event)
        
        next_token = response.get("NextToken")
        page_count += 1
        if not next_token or page_count >= max_pages:
            break
        time.sleep(0.6)
    
    if not rows:
        rows.append({
            "AccountId": account_id,
            "UserName": user_name,
            "UserArn": user_arn,
            "EventTime": "",
            "EventName": "",
            "EventSource": "",
            "SourceIPAddress": "",
            "UserAgent": "",
            "AwsRegion": "",
            "MFAAuthenticated": "",
            "ErrorCode": "",
            "Status": f"No activity found in last {lookup_days} days"
        })
    
    return rows

def parse_user_cloudtrail_event(account_id, user_name, user_arn, event):
    """Parse CloudTrail event for user activity"""
    try:
        raw_event = json.loads(event.get("CloudTrailEvent", "{}"))
        user_identity = raw_event.get("userIdentity", {}) or {}
        session_context = user_identity.get("sessionContext", {}) or {}
        session_attributes = session_context.get("attributes", {}) or {}
        
        event_username = event.get("Username", "")
        identity_arn = user_identity.get("arn", "")
        
        if event_username != user_name and user_arn not in str(identity_arn):
            return None
        
        return {
            "AccountId": account_id,
            "UserName": user_name,
            "UserArn": user_arn,
            "EventTime": str(event.get("EventTime", "")),
            "EventName": raw_event.get("eventName", event.get("EventName", "")),
            "EventSource": raw_event.get("eventSource", ""),
            "SourceIPAddress": raw_event.get("sourceIPAddress", ""),
            "UserAgent": raw_event.get("userAgent", ""),
            "AwsRegion": raw_event.get("awsRegion", ""),
            "MFAAuthenticated": session_attributes.get("mfaAuthenticated", ""),
            "ErrorCode": raw_event.get("errorCode", ""),
            "Status": "Matched"
        }
    except Exception as e:
        return {
            "AccountId": account_id,
            "UserName": user_name,
            "UserArn": user_arn,
            "EventTime": str(event.get("EventTime", "")),
            "EventName": event.get("EventName", ""),
            "EventSource": "",
            "SourceIPAddress": "",
            "UserAgent": "",
            "AwsRegion": "",
            "MFAAuthenticated": "",
            "ErrorCode": "",
            "Status": f"Unable to parse event: {str(e)}"
        }

def audit_role(account_id, role_name):
    detailed_rows = []
    risk_rows = []
    role_arn = ""
    try:
        role_response = iam.get_role(RoleName=role_name)
        role_arn = role_response["Role"]["Arn"]
    except Exception as e:
        return {
            "role_arn": "",
            "detailed_rows": [],
            "risk_rows": [{
                "AccountId": account_id,
                "RoleName": role_name,
                "PolicyName": "",
                "Finding": f"Unable to read role: {str(e)}",
                "Severity": "High",
                "Resource": "",
                "Action": ""
            }]
        }
    attached_policies = list_all_attached_role_policies(role_name)
    for policy in attached_policies:
        policy_arn = policy["PolicyArn"]
        policy_name = policy["PolicyName"]
        policy_rows, policy_risks = audit_managed_policy(
            account_id=account_id,
            role_name=role_name,
            role_arn=role_arn,
            policy_arn=policy_arn,
            policy_name_override=policy_name
        )
        detailed_rows.extend(policy_rows)
        risk_rows.extend(policy_risks)
    inline_policy_names = list_all_role_inline_policies(role_name)
    for inline_policy_name in inline_policy_names:
        try:
            response = iam.get_role_policy(
                RoleName=role_name,
                PolicyName=inline_policy_name
            )
            policy_document = normalize_policy_document(response["PolicyDocument"])
            parsed_rows, parsed_risks = parse_policy_document(
                account_id=account_id,
                input_type="Role",
                role_name=role_name,
                policy_arn="",
                role_arn=role_arn,
                policy_name=inline_policy_name,
                policy_type="Inline",
                policy_document=policy_document
            )
            detailed_rows.extend(parsed_rows)
            risk_rows.extend(parsed_risks)
        except Exception as e:
            risk_rows.append({
                "AccountId": account_id,
                "RoleName": role_name,
                "PolicyName": inline_policy_name,
                "Finding": f"Unable to read inline policy: {str(e)}",
                "Severity": "High",
                "Resource": "",
                "Action": ""
            })
    return {
        "role_arn": role_arn,
        "detailed_rows": detailed_rows,
        "risk_rows": risk_rows
    }

def list_all_attached_role_policies(role_name):
    policies = []
    marker = None
    while True:
        params = {"RoleName": role_name}
        if marker:
            params["Marker"] = marker
        response = iam.list_attached_role_policies(**params)
        policies.extend(response.get("AttachedPolicies", []))
        if response.get("IsTruncated"):
            marker = response.get("Marker")
        else:
            break
    return policies

def list_all_role_inline_policies(role_name):
    policies = []
    marker = None
    while True:
        params = {"RoleName": role_name}
        if marker:
            params["Marker"] = marker
        response = iam.list_role_policies(**params)
        policies.extend(response.get("PolicyNames", []))
        if response.get("IsTruncated"):
            marker = response.get("Marker")
        else:
            break
    return policies

def audit_managed_policy(account_id, role_name, role_arn, policy_arn, policy_name_override=None):
    try:
        policy_meta = iam.get_policy(PolicyArn=policy_arn)["Policy"]
        default_version_id = policy_meta["DefaultVersionId"]
        policy_name = policy_name_override or policy_meta["PolicyName"]
        version_response = iam.get_policy_version(
            PolicyArn=policy_arn,
            VersionId=default_version_id
        )
        policy_document = normalize_policy_document(
            version_response["PolicyVersion"]["Document"]
        )
        return parse_policy_document(
            account_id=account_id,
            input_type="Role",
            role_name=role_name,
            policy_arn=policy_arn,
            role_arn=role_arn,
            policy_name=policy_name,
            policy_type="Managed",
            policy_document=policy_document
        )
    except Exception as e:
        return [], [{
            "AccountId": account_id,
            "RoleName": role_name,
            "PolicyName": policy_arn,
            "Finding": f"Unable to read managed policy: {str(e)}",
            "Severity": "High",
            "Resource": "",
            "Action": ""
        }]

def normalize_policy_document(policy_document):
    if isinstance(policy_document, str):
        decoded = unquote(policy_document)
        return json.loads(decoded)
    return policy_document

def parse_policy_document(
    account_id,
    input_type,
    role_name,
    policy_arn,
    role_arn,
    policy_name,
    policy_type,
    policy_document
):
    rows = []
    risks = []
    statements = policy_document.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    for statement in statements:
        sid = statement.get("Sid", "")
        effect = statement.get("Effect", "")
        actions = statement.get("Action", [])
        not_actions = statement.get("NotAction", [])
        resources = statement.get("Resource", [])
        not_resources = statement.get("NotResource", [])
        condition = statement.get("Condition", {})
        actions = ensure_list(actions)
        not_actions = ensure_list(not_actions)
        resources = ensure_list(resources)
        not_resources = ensure_list(not_resources)
        action_items = actions if actions else [f"NOT_ACTION::{item}" for item in not_actions]
        resource_items = resources if resources else [f"NOT_RESOURCE::{item}" for item in not_resources]
        if not resource_items:
            resource_items = [""]
        for action in action_items:
            service, action_name = split_action(action)
            access_type = classify_access_type(service, action_name)
            full_action = f"{service}:{action_name}" if service != "Unknown" else action_name
            for resource in resource_items:
                resource_level = classify_resource_level(service, resource)
                risk_flag = identify_risk_flag(
                    effect=effect,
                    service=service,
                    action_name=action_name,
                    resource=resource,
                    condition=condition
                )
                row = {
                    "AccountId": account_id,
                    "InputType": input_type,
                    "RoleName": role_name,
                    "PolicyArn": policy_arn,
                    "RoleArn": role_arn,
                    "PolicyName": policy_name,
                    "PolicyType": policy_type,
                    "StatementSid": sid,
                    "Effect": effect,
                    "Service": service,
                    "Action": action_name,
                    "FullAction": full_action,
                    "AccessType": access_type,
                    "Resource": resource,
                    "ResourceLevel": resource_level,
                    "Condition": json.dumps(condition) if condition else "",
                    "RiskFlag": risk_flag
                }
                rows.append(row)
                if risk_flag:
                    risks.append({
                        "AccountId": account_id,
                        "RoleName": role_name,
                        "PolicyName": policy_name,
                        "Finding": risk_flag,
                        "Severity": classify_risk_severity(risk_flag),
                        "Resource": resource,
                        "Action": full_action
                    })
    return rows, risks

def ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]

def split_action(action):
    if action.startswith("NOT_ACTION::"):
        clean_action = action.replace("NOT_ACTION::", "")
        if ":" in clean_action:
            service, action_name = clean_action.split(":", 1)
            return f"NotAction-{service}", action_name
        return "NotAction-Unknown", clean_action
    if ":" in action:
        service, action_name = action.split(":", 1)
        return service, action_name
    return "Unknown", action

def classify_access_type(service, action_name):
    action_lower = action_name.lower()
    if action_name == "*":
        return "Admin"
    if "*" in action_name:
        return "Wildcard"
    read_prefixes = [
        "get", "describe", "query", "scan", "batchget", "read",
        "lookup", "select", "head", "receive"
    ]
    list_prefixes = [
        "list"
    ]
    write_prefixes = [
        "put", "create", "update", "modify", "attach", "detach",
        "start", "stop", "restart", "run", "invoke", "send", "publish",
        "tag", "untag", "batchwrite", "copy", "restore"
    ]
    delete_prefixes = [
        "delete", "remove", "terminate", "purge"
    ]
    permission_prefixes = [
        "assume", "passrole", "grant", "revoke", "authorize",
        "addrole", "createrole", "putrolepolicy", "attachrolepolicy"
    ]
    for prefix in delete_prefixes:
        if action_lower.startswith(prefix):
            return "Delete"
    for prefix in list_prefixes:
        if action_lower.startswith(prefix):
            return "List"
    for prefix in read_prefixes:
        if action_lower.startswith(prefix):
            return "Read"
    for prefix in write_prefixes:
        if action_lower.startswith(prefix):
            return "Write"
    for prefix in permission_prefixes:
        if action_lower.startswith(prefix):
            return "PermissionManagement"
    if service == "iam":
        return "PermissionManagement"
    return "Other"

def classify_resource_level(service, resource):
    if resource == "*":
        return "Account/Wildcard"
    if resource.startswith("NOT_RESOURCE::"):
        return "NotResource"
    if service == "s3":
        return classify_s3_resource(resource)
    if service == "dynamodb":
        if ":table/" in resource and "/index/" in resource:
            return "DynamoDB Index Level"
        if ":table/" in resource:
            return "DynamoDB Table Level"
        return "DynamoDB Resource Level"
    if service == "lambda":
        if ":function:" in resource:
            return "Lambda Function Level"
        return "Lambda Resource Level"
    if service == "sqs":
        return "SQS Queue Level"
    if service == "sns":
        return "SNS Topic Level"
    if service == "kms":
        return "KMS Key Level"
    if service == "secretsmanager":
        return "Secret Level"
    if service == "logs":
        if ":log-group:" in resource:
            return "CloudWatch Log Group Level"
        return "CloudWatch Logs Resource Level"
    if service == "glue":
        return "Glue Resource Level"
    if service == "athena":
        return "Athena Resource Level"
    if service == "rds":
        return "RDS Resource Level"
    if service == "ec2":
        return "EC2 Resource Level"
    if resource.startswith("arn:"):
        return "Resource ARN Level"
    return "Unknown/Global"

def classify_s3_resource(resource):
    if resource == "*":
        return "S3 Account/Wildcard"
    bucket_only_pattern = r"^arn:aws:s3:::[^/]+$"
    object_or_prefix_pattern = r"^arn:aws:s3:::[^/]+/.+"
    if re.match(bucket_only_pattern, resource):
        return "S3 Bucket Level"
    if re.match(object_or_prefix_pattern, resource):
        if resource.endswith("/*"):
            return "S3 Prefix/Folder Level"
        return "S3 Object Level"
    return "S3 Resource Level"

def identify_risk_flag(effect, service, action_name, resource, condition):
    if effect == "Deny":
        return ""
    full_action = f"{service}:{action_name}".lower()
    if action_name == "*":
        return "Full admin or service-level wildcard action"
    if "*" in action_name and resource == "*":
        return "Wildcard action with wildcard resource"
    if resource == "*":
        return "Wildcard resource access"
    if full_action in ["iam:passrole", "sts:assumerole"]:
        return "Sensitive role delegation permission"
    if service == "iam" and "*" in action_name:
        return "IAM wildcard permission"
    sensitive_delete_actions = [
        "s3:deletebucket",
        "s3:deleteobject",
        "kms:schedulekeydeletion",
        "secretsmanager:deletesecret",
        "rds:deletedbinstance",
        "dynamodb:deletetable",
        "lambda:deletefunction"
    ]
    if full_action in sensitive_delete_actions:
        return "Sensitive delete permission"
    if condition:
        return ""
    return ""

def classify_risk_severity(risk_flag):
    risk_lower = risk_flag.lower()
    high_keywords = [
        "admin",
        "wildcard action with wildcard resource",
        "iam wildcard",
        "role delegation"
    ]
    medium_keywords = [
        "wildcard resource",
        "delete permission"
    ]
    for keyword in high_keywords:
        if keyword in risk_lower:
            return "High"
    for keyword in medium_keywords:
        if keyword in risk_lower:
            return "Medium"
    return "Low"

def build_service_summary(detailed_rows):
    summary = defaultdict(lambda: {
        "Read": "No",
        "Write": "No",
        "List": "No",
        "Delete": "No",
        "Admin": "No",
        "Wildcard": "No",
        "PermissionManagement": "No",
        "Other": "No",
        "Resources": set(),
        "Actions": set()
    })
    for row in detailed_rows:
        key = (
            row.get("AccountId", ""),
            row.get("RoleName", ""),
            row.get("PolicyName", ""),
            row.get("Service", "")
        )
        access_type = row.get("AccessType", "Other")
        resource = row.get("Resource", "")
        full_action = row.get("FullAction", "")
        valid_access_types = ["Read", "Write", "List", "Delete", "Admin", "Wildcard", "PermissionManagement"]
        if access_type in valid_access_types:
            summary[key][access_type] = "Yes"
        else:
            summary[key]["Other"] = "Yes"
        if resource:
            summary[key]["Resources"].add(resource)
        if full_action:
            summary[key]["Actions"].add(full_action)
    rows = []
    for (account_id, role_name, policy_name, service), values in summary.items():
        rows.append({
            "AccountId": account_id,
            "RoleName": role_name,
            "PolicyName": policy_name,
            "Service": service,
            "Read": values["Read"],
            "Write": values["Write"],
            "List": values["List"],
            "Delete": values["Delete"],
            "Admin": values["Admin"],
            "Wildcard": values["Wildcard"],
            "PermissionManagement": values["PermissionManagement"],
            "Other": values["Other"],
            "ActionCount": len(values["Actions"]),
            "ResourceCount": len(values["Resources"])
        })
    return rows

def get_last_access_details(account_id, role_name, role_arn):
    rows = []
    try:
        generate_response = iam.generate_service_last_accessed_details(
            Arn=role_arn,
            Granularity="ACTION_LEVEL"
        )
        job_id = generate_response["JobId"]
        response = None
        for _ in range(10):
            response = iam.get_service_last_accessed_details(JobId=job_id)
            if response.get("JobStatus") in ["COMPLETED", "FAILED"]:
                break
            time.sleep(1)
        if not response:
            return [{
                "AccountId": account_id,
                "RoleName": role_name,
                "RoleArn": role_arn,
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": "No response from IAM last accessed API"
            }]
        if response.get("JobStatus") != "COMPLETED":
            return [{
                "AccountId": account_id,
                "RoleName": role_name,
                "RoleArn": role_arn,
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": f"Job status: {response.get('JobStatus')}"
            }]
        while True:
            services = response.get("ServicesLastAccessed", [])
            for service in services:
                tracked_actions = service.get("TrackedActionsLastAccessed", [])
                if tracked_actions:
                    for tracked_action in tracked_actions:
                        rows.append({
                            "AccountId": account_id,
                            "RoleName": role_name,
                            "RoleArn": role_arn,
                            "ServiceName": service.get("ServiceName", ""),
                            "ServiceNamespace": service.get("ServiceNamespace", ""),
                            "ActionName": tracked_action.get("ActionName", ""),
                            "LastAuthenticated": str(tracked_action.get("LastAccessedTime", "")),
                            "LastAuthenticatedRegion": service.get("LastAuthenticatedRegion", ""),
                            "LastAuthenticatedEntity": service.get("LastAuthenticatedEntity", ""),
                            "TotalAuthenticatedEntities": service.get("TotalAuthenticatedEntities", ""),
                            "Status": "Completed"
                        })
                else:
                    rows.append({
                        "AccountId": account_id,
                        "RoleName": role_name,
                        "RoleArn": role_arn,
                        "ServiceName": service.get("ServiceName", ""),
                        "ServiceNamespace": service.get("ServiceNamespace", ""),
                        "ActionName": "",
                        "LastAuthenticated": str(service.get("LastAuthenticated", "")),
                        "LastAuthenticatedRegion": service.get("LastAuthenticatedRegion", ""),
                        "LastAuthenticatedEntity": service.get("LastAuthenticatedEntity", ""),
                        "TotalAuthenticatedEntities": service.get("TotalAuthenticatedEntities", ""),
                        "Status": "Completed"
                    })
            marker = response.get("Marker")
            if response.get("IsTruncated") and marker:
                response = iam.get_service_last_accessed_details(
                    JobId=job_id,
                    Marker=marker
                )
            else:
                break
        if not rows:
            rows.append({
                "AccountId": account_id,
                "RoleName": role_name,
                "RoleArn": role_arn,
                "ServiceName": "",
                "ServiceNamespace": "",
                "ActionName": "",
                "LastAuthenticated": "",
                "LastAuthenticatedRegion": "",
                "LastAuthenticatedEntity": "",
                "TotalAuthenticatedEntities": "",
                "Status": "No last accessed details returned"
            })
        return rows
    except Exception as e:
        return [{
            "AccountId": account_id,
            "RoleName": role_name,
            "RoleArn": role_arn,
            "ServiceName": "",
            "ServiceNamespace": "",
            "ActionName": "",
            "LastAuthenticated": "",
            "LastAuthenticatedRegion": "",
            "LastAuthenticatedEntity": "",
            "TotalAuthenticatedEntities": "",
            "Status": f"Error: {str(e)}"
        }]

def get_role_usage_from_cloudtrail(account_id, role_name, role_arn, lookup_days, max_pages):
    rows = []
    event_names = [
        "AssumeRole",
        "AssumeRoleWithSAML",
        "AssumeRoleWithWebIdentity"
    ]
    start_time = datetime.now(timezone.utc) - timedelta(days=lookup_days)
    end_time = datetime.now(timezone.utc)
    for event_name in event_names:
        next_token = None
        page_count = 0
        while True:
            params = {
                "LookupAttributes": [
                    {
                        "AttributeKey": "EventName",
                        "AttributeValue": event_name
                    }
                ],
                "StartTime": start_time,
                "EndTime": end_time,
                "MaxResults": 50
            }
            if next_token:
                params["NextToken"] = next_token
            try:
                response = cloudtrail.lookup_events(**params)
            except Exception as e:
                rows.append({
                    "AccountId": account_id,
                    "RoleName": role_name,
                    "RoleArn": role_arn,
                    "EventTime": "",
                    "EventName": event_name,
                    "WhoAssumedRole": "",
                    "SourceIdentity": "",
                    "RoleSessionName": "",
                    "SourceIPAddress": "",
                    "UserAgent": "",
                    "AwsRegion": "",
                    "MFAAuthenticated": "",
                    "ErrorCode": "",
                    "Status": f"Error reading CloudTrail: {str(e)}"
                })
                break
            events = response.get("Events", [])
            for event in events:
                parsed_row = parse_cloudtrail_assume_role_event(
                    account_id=account_id,
                    target_role_name=role_name,
                    target_role_arn=role_arn,
                    event=event
                )
                if parsed_row:
                    rows.append(parsed_row)
            next_token = response.get("NextToken")
            page_count += 1
            if not next_token or page_count >= max_pages:
                break
            time.sleep(0.6)
    if not rows:
        rows.append({
            "AccountId": account_id,
            "RoleName": role_name,
            "RoleArn": role_arn,
            "EventTime": "",
            "EventName": "",
            "WhoAssumedRole": "",
            "SourceIdentity": "",
            "RoleSessionName": "",
            "SourceIPAddress": "",
            "UserAgent": "",
            "AwsRegion": "",
            "MFAAuthenticated": "",
            "ErrorCode": "",
            "Status": f"No AssumeRole activity found in last {lookup_days} days by LookupEvents"
        })
    return rows

def parse_cloudtrail_assume_role_event(account_id, target_role_name, target_role_arn, event):
    try:
        raw_event = json.loads(event.get("CloudTrailEvent", "{}"))
        request_params = raw_event.get("requestParameters", {}) or {}
        response_elements = raw_event.get("responseElements", {}) or {}
        user_identity = raw_event.get("userIdentity", {}) or {}
        session_context = user_identity.get("sessionContext", {}) or {}
        session_attributes = session_context.get("attributes", {}) or {}
        request_role_arn = request_params.get("roleArn", "")
        role_session_name = request_params.get("roleSessionName", "")
        assumed_role_user = response_elements.get("assumedRoleUser", {}) or {}
        assumed_role_arn = assumed_role_user.get("arn", "")
        matched = False
        if request_role_arn == target_role_arn:
            matched = True
        if f":assumed-role/{target_role_name}/" in assumed_role_arn:
            matched = True
        if not matched:
            return None
        source_identity = (
            request_params.get("sourceIdentity")
            or session_context.get("sourceIdentity")
            or ""
        )
        who_assumed_role = (
            user_identity.get("arn")
            or user_identity.get("principalId")
            or event.get("Username", "")
        )
        return {
            "AccountId": account_id,
            "RoleName": target_role_name,
            "RoleArn": target_role_arn,
            "EventTime": str(event.get("EventTime", "")),
            "EventName": raw_event.get("eventName", event.get("EventName", "")),
            "WhoAssumedRole": who_assumed_role,
            "SourceIdentity": source_identity,
            "RoleSessionName": role_session_name,
            "SourceIPAddress": raw_event.get("sourceIPAddress", ""),
            "UserAgent": raw_event.get("userAgent", ""),
            "AwsRegion": raw_event.get("awsRegion", ""),
            "MFAAuthenticated": session_attributes.get("mfaAuthenticated", ""),
            "ErrorCode": raw_event.get("errorCode", ""),
            "Status": "Matched"
        }
    except Exception as e:
        return {
            "AccountId": account_id,
            "RoleName": target_role_name,
            "RoleArn": target_role_arn,
            "EventTime": str(event.get("EventTime", "")),
            "EventName": event.get("EventName", ""),
            "WhoAssumedRole": event.get("Username", ""),
            "SourceIdentity": "",
            "RoleSessionName": "",
            "SourceIPAddress": "",
            "UserAgent": "",
            "AwsRegion": "",
            "MFAAuthenticated": "",
            "ErrorCode": "",
            "Status": f"Unable to parse CloudTrail event: {str(e)}"
        }

def write_excel_report(
    local_path,
    detailed_rows,
    summary_rows,
    risk_rows,
    last_access_rows,
    role_usage_rows,
):
    """Write Excel report for roles with all 5 tabs"""
    wb = Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)
    add_sheet(wb, "Detailed Permissions", detailed_rows)
    add_sheet(wb, "Service Summary", summary_rows)
    add_sheet(wb, "Risk Findings", risk_rows)
    add_sheet(wb, "Last Access", last_access_rows)
    add_sheet(wb, "Role Usage CloudTrail", role_usage_rows)
    wb.save(local_path)
def write_excel_report_for_role(
    local_path,
    detailed_rows,
    summary_rows,
    risk_rows,
    last_access_rows,
    role_usage_rows
):
    """Write Excel report for roles with all 5 tabs"""
    write_excel_report(local_path, detailed_rows, summary_rows, risk_rows, last_access_rows, role_usage_rows)

def write_excel_report_for_policy(local_path, detailed_rows, summary_rows, risk_rows):
    """Write Excel report for policies with only 3 relevant tabs"""
    wb = Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)
    add_sheet(wb, "Detailed Permissions", detailed_rows)
    add_sheet(wb, "Service Summary", summary_rows)
    add_sheet(wb, "Risk Findings", risk_rows)
    wb.save(local_path)


def create_user_excel_report(local_path, detailed_rows, summary_rows, risk_rows, last_access_rows, user_activity_rows):
    """Write Excel report for IAM users with all 5 tabs"""
    wb = Workbook()
    default_sheet = wb.active
    wb.remove(default_sheet)
    add_sheet(wb, "Detailed Permissions", detailed_rows)
    add_sheet(wb, "Service Summary", summary_rows)
    add_sheet(wb, "Risk Findings", risk_rows)
    add_sheet(wb, "Last Access", last_access_rows)
    add_sheet(wb, "User Activity CloudTrail", user_activity_rows)
    wb.save(local_path)

def add_sheet(wb, sheet_name, rows):
    ws = wb.create_sheet(title=sheet_name)
    if not rows:
        rows = [{"Status": "No data"}]
    headers = list(rows[0].keys())
    header_fill = PatternFill(
        start_color="1F4E78",
        end_color="1F4E78",
        fill_type="solid"
    )
    header_font = Font(color="FFFFFF", bold=True)
    for col_index, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_index, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for row_index, row in enumerate(rows, start=2):
        for col_index, header in enumerate(headers, start=1):
            value = row.get(header, "")
            ws.cell(row=row_index, column=col_index, value=value)
    ws.freeze_panes = "A2"
    for col_index, header in enumerate(headers, start=1):
        column_letter = get_column_letter(col_index)
        max_length = len(str(header))
        for row_index in range(2, min(ws.max_row + 1, 200)):
            cell_value = ws.cell(row=row_index, column=col_index).value
            if cell_value is not None:
                max_length = max(max_length, len(str(cell_value)))
        ws.column_dimensions[column_letter].width = min(max_length + 2, 80)

def sanitize_name(name):
    safe_name = (
        name
        .replace("/", "_")
        .replace("\\", "_")
        .replace(" ", "_")
        .replace(":", "_")
    )
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", safe_name)
    return safe_name
