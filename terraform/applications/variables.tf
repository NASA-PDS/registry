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

variable "node_nucleus_harvest_iam_roles" {
  description = "Map of discipline node names to their IAM role ARNs (e.g., { geo = 'arn:aws:iam::...' }). Keys should match entries in node_list."
  type        = map(string)
  default     = {}
}

variable "venue" {
  description = "Deployment venue (e.g. pds-en-dev, prod), used in resource tags across all modules"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the OpenSearch Serverless VPC endpoint will be created (required if create_vpc_endpoint is true)"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs for the VPC endpoint (required if create_vpc_endpoint is true) and for the Registry API ECS Service"
  type        = list(string)
  default     = []
}

variable "public_subnet_ids" {
  description = "Subnet IDs for the registry API load balancer"
  type        = list(string)
  default     = []
}

variable "security_group_ids" {
  description = "Security group IDs for the VPC endpoint (if not provided, a default security group will be created)"
  type        = list(string)
  default     = []
}

# Lambda Configuration
# Lambda execution role is now created by the IAM module
# variable "lambda_execution_role_arn" is no longer needed

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

variable "aws_s3_bucket_logs_id" {
  description = "ID of the S3 bucket used for registry-api load balancer access logs"
  type        = string
  default     = ""
}

variable "registry_api_docker_image" {
  description = "Docker image URI for the registry-api ECS service"
  type        = string
  default     = ""
}

variable "registry_api_ecs_service_security_group" {
  description = "Security group associated ot the ECS Service"
  type        = string
  default     = ""
}


variable "acm_certificate_arn" {
  description = "ACM Certificate ARN used for HTTPS access to the Registry API load balancer, re-use the certificate of the cloudfront distribution DNS"
  type        = string
  default     = ""
}

# registry-sweepers variables

variable "managedby" {
  description = "Person or system responsible for the deployment"
  type        = string
}

variable "aoss_endpoint" {
  description = "Registry AOSS endpoint URL"
  type        = string
}

variable "sweepers_image_uri" {
  description = "registry-sweepers Docker image URI"
  type        = string
}

variable "mwaa_execution_role_name" {
  description = "Name of the MWAA execution role that needs iam:PassRole to launch ECS tasks"
  type        = string
  default     = ""
}

variable "sweepers_nodes" {
  description = "Map of node IDs to ECS resource allocations for registry-sweepers"
  type = map(object({
    cpu             = number
    memory          = number
    additional_args = optional(string)
  }))
}

# registry-api variables

variable "registry_api_node_name_abbr" {
  description = "Node name abbreviation for registry-api"
  type        = string
  default     = "en"
}

variable "registry_api_spring_boot_args" {
  description = "Spring Boot arguments for registry-api, including OpenSearch endpoint"
  type        = string
}

variable "registry_api_lb_security_groups" {
  description = "Security group IDs for the registry-api load balancer"
  type        = list(string)
  default     = []
}

variable "registry_api_ecs_task_role" {
  description = "IAM role ARN for the registry-api ECS task"
  type        = string
}

variable "registry_api_ecs_task_execution_role" {
  description = "IAM role ARN for the registry-api ECS task execution"
  type        = string
}

variable "registry_api_cloudfront_dns" {
  description = "DNS of the CloudFront distribution providing access to the registry-api"
  type        = string
}
