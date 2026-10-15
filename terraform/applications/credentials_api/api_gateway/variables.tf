variable "api_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "api_description" {
  description = "Description of the API Gateway"
  type        = string
  default     = ""
}

variable "stage_name" {
  description = "Deployment stage name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "lambda_function_name" {
  description = "Name of the Lambda function to integrate with"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function to integrate with"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all API Gateway resources"
  type        = map(string)
  default     = {}
}
