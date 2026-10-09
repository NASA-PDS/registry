output "api_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_arn" {
  description = "ARN of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.arn
}

output "api_endpoint" {
  description = "Base URL of the API Gateway"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "credentials_endpoint" {
  description = "Full URL for the /credentials endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/credentials"
}

output "stage_name" {
  description = "Name of the deployment stage"
  value       = aws_api_gateway_stage.main.stage_name
}

output "execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.main.execution_arn
}
