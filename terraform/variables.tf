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
