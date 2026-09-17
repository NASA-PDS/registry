# Root Outputs
# These outputs expose values from the credentials_api module

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.credentials_api.lambda_function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.credentials_api.lambda_function_arn
}

output "lambda_log_group_name" {
  description = "Name of the Lambda CloudWatch Log Group"
  value       = module.credentials_api.lambda_log_group_name
}

output "lambda_log_group_arn" {
  description = "ARN of the Lambda CloudWatch Log Group"
  value       = module.credentials_api.lambda_log_group_arn
}

output "cognito_jwks_url" {
  description = "Cognito JWKS URL used for JWT token validation"
  value       = module.credentials_api.cognito_jwks_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.credentials_api.api_gateway_id
}

output "api_gateway_endpoint" {
  description = "Base URL of the API Gateway"
  value       = module.credentials_api.api_gateway_endpoint
}

output "credentials_endpoint" {
  description = "Full URL for the GET /credentials endpoint"
  value       = module.credentials_api.credentials_endpoint
}

output "node_list" {
  description = "List of discipline nodes"
  value       = module.credentials_api.node_list
}

# registry-sweepers outputs

output "sweepers_task_definition_arns" {
  description = "Map of node name to ECS task definition ARN"
  value       = module.registry_sweepers.sweepers_task_definition_arns
}

output "sweepers_log_group_names" {
  description = "Map of node name to CloudWatch log group name"
  value       = module.registry_sweepers.sweepers_log_group_names
}

output "sweepers_task_role_arn" {
  description = "Sweeper task role ARN needed to update the OpenSearch data access policy"
  value       = module.registry_sweepers.sweepers_task_role_arn
}

# registry-api outputs

output "registry_api_load_balancer_domain" {
  description = "Registry API load balancer domain"
  value       = module.registry_api.load_balancer_domain
}
