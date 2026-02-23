output "lambda_function_name" {
  value = aws_lambda_function.this.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.this.arn
}

output "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function (used by API Gateway)"
  value       = aws_lambda_function.this.invoke_arn
}

output "lambda_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.arn
}

output "lambda_log_group_name" {
  description = "Name of the CloudWatch Log Group for Lambda function"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "cognito_jwks_url" {
  description = "Cognito JWKS URL used for JWT token validation"
  value       = local.jwks_url
}

