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

output "vpc_endpoint_id" {
  description = "The ID of the created VPC endpoint"
  value       = aws_vpc_endpoint.opensearch_serverless.id
}

output "vpc_endpoint_dns_entries" {
  description = "DNS entries for the VPC endpoint"
  value       = aws_vpc_endpoint.opensearch_serverless.dns_entry
}

output "security_group_id" {
  description = "The ID of the security group created for the VPC endpoint"
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
