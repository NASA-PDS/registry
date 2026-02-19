# Root Outputs
# These outputs expose values from the sub-modules

# OpenSearch Collection Outputs
output "collection_id" {
  description = "The ID of the OpenSearch Serverless collection"
  value       = module.opensearch.collection_id
}

output "collection_arn" {
  description = "The ARN of the OpenSearch Serverless collection"
  value       = module.opensearch.collection_arn
}

output "collection_endpoint" {
  description = "The endpoint URL for the OpenSearch Serverless collection"
  value       = module.opensearch.collection_endpoint
}

output "dashboard_endpoint" {
  description = "The OpenSearch Dashboards endpoint URL"
  value       = module.opensearch.dashboard_endpoint
}

output "collection_name" {
  description = "The name of the OpenSearch Serverless collection"
  value       = module.opensearch.collection_name
}

output "collection_type" {
  description = "The type of the OpenSearch Serverless collection"
  value       = module.opensearch.collection_type
}

# VPC Endpoint Outputs
output "vpc_endpoint_id" {
  description = "The ID of the created VPC endpoint (if created)"
  value       = module.opensearch.vpc_endpoint_id
}

output "vpc_endpoint_dns_entries" {
  description = "DNS entries for the VPC endpoint"
  value       = module.opensearch.vpc_endpoint_dns_entries
}

output "security_group_id" {
  description = "The ID of the security group created for the VPC endpoint (if created)"
  value       = module.opensearch.security_group_id
}

# Security Policy Outputs
output "network_policy_name" {
  description = "The name of the network security policy (update this in AWS Console to change Access Type)"
  value       = module.opensearch.network_policy_name
}

output "network_policy_version" {
  description = "The version of the network security policy"
  value       = module.opensearch.network_policy_version
}

# External Policies Outputs
output "api_dashboard_policy_arn" {
  description = "The ARN of the IAM policy for OpenSearch admin access"
  value       = module.external_policies.api_dashboard_policy_arn
}

output "api_only_policy_arn" {
  description = "The ARN of the IAM policy for OpenSearch API-only access (limited writer)"
  value       = module.external_policies.api_only_policy_arn
}
