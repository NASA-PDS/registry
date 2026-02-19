output "admin_policy_arn" {
  description = "The ARN of the IAM policy for OpenSearch admin access"
  value       = aws_iam_policy.opensearch_admin_access.arn
}

output "admin_policy_name" {
  description = "The name of the IAM policy for OpenSearch admin access"
  value       = aws_iam_policy.opensearch_admin_access.name
}

output "admin_policy_id" {
  description = "The ID of the IAM policy for OpenSearch admin access"
  value       = aws_iam_policy.opensearch_admin_access.id
}

output "api_only_policy_arn" {
  description = "The ARN of the IAM policy for OpenSearch API-only access (limited writer)"
  value       = aws_iam_policy.opensearch_api_only_access.arn
}

output "api_only_policy_name" {
  description = "The name of the IAM policy for OpenSearch API-only access (limited writer)"
  value       = aws_iam_policy.opensearch_api_only_access.name
}

output "api_only_policy_id" {
  description = "The ID of the IAM policy for OpenSearch API-only access (limited writer)"
  value       = aws_iam_policy.opensearch_api_only_access.id
}
