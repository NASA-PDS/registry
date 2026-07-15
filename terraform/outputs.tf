# Root Outputs
# These outputs expose values from the sub-modules

# OpenSearch Collection Outputs

locals {
  opensearch_pre_created_message = "unknown refer to SSM parameter /pds/registry/opensearch_serverless/collection_arn to find out about the opensearch instance used"
}


output "collection_endpoint" {
  description = "The endpoint URL for the OpenSearch Serverless collection"
  value       = var.recreate_opensearch ? module.opensearch[0].collection_endpoint : local.opensearch_pre_created_message
}

output "dashboard_endpoint" {
  description = "The OpenSearch Dashboards endpoint URL"
  value       = var.recreate_opensearch ? module.opensearch[0].dashboard_endpoint : local.opensearch_pre_created_message
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

output "node_list" {
  description = "List of discipline nodes"
  value       = var.node_list
}
