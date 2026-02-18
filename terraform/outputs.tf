output "collection_id" {
  description = "The ID of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.id
}

output "collection_arn" {
  description = "The ARN of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.arn
}

output "collection_endpoint" {
  description = "The endpoint URL for the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.collection_endpoint
}

output "dashboard_endpoint" {
  description = "The OpenSearch Dashboards endpoint URL"
  value       = aws_opensearchserverless_collection.main.dashboard_endpoint
}

output "collection_name" {
  description = "The name of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.name
}

output "collection_type" {
  description = "The type of the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.type
}

output "admin_policy_arn" {
  description = "The ARN of the IAM policy for OpenSearch admin access"
  value       = aws_iam_policy.opensearch_admin_access.arn
}

output "admin_policy_ssm_parameter" {
  description = "The SSM parameter name storing the admin policy ARN"
  value       = aws_ssm_parameter.admin_policy_arn.name
}

output "admin_roles_configured" {
  description = "List of admin roles currently configured for data access"
  value       = local.data_access_principals
}

output "deployment_stage" {
  description = "Current deployment stage based on admin roles configuration"
  value = length(local.data_access_principals) > 0 ? "Stage 3: Complete - Admin roles configured" : "Stage 1: Initial - Awaiting admin role creation"
}

output "vpc_endpoint_id" {
  description = "The ID of the created VPC endpoint (if created)"
  value       = aws_vpc_endpoint.opensearch_serverless.id
}

output "vpc_endpoint_dns_entries" {
  description = "DNS entries for the VPC endpoint"
  value       = aws_vpc_endpoint.opensearch_serverless.dns_entry
}

output "security_group_id" {
  description = "The ID of the security group created for the VPC endpoint (if created)"
  value       = aws_security_group.vpce.id
}

output "network_policy_name" {
  description = "The name of the network security policy (update this in AWS Console to change Access Type)"
  value       = aws_opensearchserverless_security_policy.network.name
}

output "network_policy_version" {
  description = "The version of the network security policy"
  value       = aws_opensearchserverless_security_policy.network.policy_version
}
