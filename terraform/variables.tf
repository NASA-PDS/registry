variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "AWS profile to use for authentication"
  type        = string
  default     = ""
}


variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
  default     = "registry-collection"
}

variable "standby_replicas" {
  description = "Enable standby replicas for the collection (ENABLED or DISABLED)"
  type        = string
  default     = "DISABLED"

  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.standby_replicas)
    error_message = "Standby replicas must be either ENABLED or DISABLED"
  }
}

variable "admin_roles" {
  description = "List of AWS principals (ARNs) allowed to access the OpenSearch collection with admin permissions."
  type        = list(string)
  default     = []
}

variable "readonly_roles" {
  description = "List of AWS principals (ARNs) allowed to access the OpenSearch collection with readonly permissions."
  type        = list(string)
  default     = []
}

variable "node_list" {
  description = "List of discipline nodes (e.g., ['geo', 'atm', 'img']). For each node, a read-write access rule will be created for the pattern '{node}-*' with the principal 'arn:aws:iam::{account_id}:role/pds-registry-{node}-read-write-aoss-role'"
  type        = list(string)
  default     = []
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "registry"
    ManagedBy   = "terraform"
  }
}


variable "vpc_id" {
  description = "VPC ID where the OpenSearch Serverless VPC endpoint will be created (required if create_vpc_endpoint is true)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for the VPC endpoint (required if create_vpc_endpoint is true)"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for the VPC endpoint (if not provided, a default security group will be created)"
  type        = list(string)
  default     = []
}

# Lambda Configuration
variable "lambda_execution_role_arn" {
  description = "IAM execution role ARN for Lambda function (created in separate IAM infrastructure repository)"
  type        = string
  default     = ""
}

variable "lambda_runtime" {
  description = "Lambda runtime version"
  type        = string
  default     = "python3.13"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "cognito_allowed_groups" {
  description = "List of Cognito groups allowed to access the Lambda function"
  type        = list(string)
  default     = []
}

variable "cognito_user_pool_id" {
  description = "Cognito User Pool ID for Lambda authentication"
  type        = string
  default     = ""
}

variable "cognito_identity_pool_id" {
  description = "Cognito Identity Pool ID for Lambda authentication"
  type        = string
  default     = ""
}

# API Gateway Configuration
variable "api_gateway_name" {
  description = "Name of the API Gateway"
  type        = string
  default     = "pds-registry-api"
}

variable "api_gateway_stage_name" {
  description = "API Gateway deployment stage name"
  type        = string
  default     = "prod"
}
