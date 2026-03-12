# Root Outputs
# These outputs expose values from the sub-modules

# OpenSearch Collection Outputs


output "collection_endpoint" {
  description = "The endpoint URL for the OpenSearch Serverless collection"
  value       = module.opensearch.collection_endpoint
}

output "dashboard_endpoint" {
  description = "The OpenSearch Dashboards endpoint URL"
  value       = module.opensearch.dashboard_endpoint
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


# Lambda Outputs
output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.lambda.lambda_function_arn
}

output "lambda_log_group_name" {
  description = "Name of the Lambda CloudWatch Log Group"
  value       = module.lambda.lambda_log_group_name
}

output "lambda_log_group_arn" {
  description = "ARN of the Lambda CloudWatch Log Group"
  value       = module.lambda.lambda_log_group_arn
}

output "cognito_jwks_url" {
  description = "Cognito JWKS URL used for JWT token validation"
  value       = module.lambda.cognito_jwks_url
}


# API Gateway Outputs
output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.api_id
}

output "api_gateway_endpoint" {
  description = "Base URL of the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "credentials_endpoint" {
  description = "Full URL for the GET /credentials endpoint"
  value       = module.api_gateway.credentials_endpoint
}
