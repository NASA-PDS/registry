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
