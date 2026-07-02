
variable "runtime" {
  description = "Lambda runtime."
  type        = string
  default     = "python3.13"
}

variable "lambda_execution_role_arn" {
  description = "IAM execution role ARN for Lambda function"
  type        = string
}

variable "timeout" {
  description = "Lambda timeout."
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory size."
  type        = number
  default     = 512
}

variable "cognito_allowed_groups" {
  description = "List of Cognito groups allowed to access the Lambda function"
  type        = list(string)
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
}

variable "cognito_identity_pool_id" {
  description = "Cognito Identity Pool ID"
  type        = string
}

variable "aws_region" {
  description = "AWS region where Cognito User Pool is deployed"
  type        = string
}

variable "vpc_subnet_ids" {
  description = "List of subnet IDs for Lambda VPC config."
  type        = list(string)
  default     = []
}

variable "vpc_security_group_ids" {
  description = "List of security group IDs for Lambda VPC config."
  type        = list(string)
  default     = []
}

variable "common_tags" {
  description = "Common tags to apply to all Lambda resources"
  type        = map(string)
  default     = {}
}
