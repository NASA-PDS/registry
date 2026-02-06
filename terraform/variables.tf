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

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "registry"
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

variable "collection_type" {
  description = "Type of OpenSearch Serverless collection (SEARCH, TIMESERIES, or VECTORSEARCH)"
  type        = string
  default     = "SEARCH"

  validation {
    condition     = contains(["SEARCH", "TIMESERIES", "VECTORSEARCH"], var.collection_type)
    error_message = "Collection type must be one of: SEARCH, TIMESERIES, VECTORSEARCH"
  }
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

variable "admin_console_role" {
  description = "List of AWS principals (ARNs) allowed to access the OpenSearch collection with admin permissions from the AWS console."
  type        = list(string)
  default     = []
}

variable "use_ssm_for_admin_role" {
  description = "Read admin role ARN from SSM Parameter Store at /pds/infra/iam/roles/pds_registry_admin_role_arn (set to true after IAM role is created in separate terraform repo)"
  type        = bool
  default     = false
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "registry"
    ManagedBy   = "terraform"
  }
}

variable "enable_public_access" {
  description = "Enable public access to the OpenSearch collection"
  type        = bool
  default     = false
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
