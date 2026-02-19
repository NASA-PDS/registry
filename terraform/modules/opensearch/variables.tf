variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "standby_replicas" {
  description = "Enable standby replicas for the collection (ENABLED or DISABLED)"
  type        = string

  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.standby_replicas)
    error_message = "Standby replicas must be either ENABLED or DISABLED"
  }
}

variable "vpc_id" {
  description = "VPC ID where the OpenSearch Serverless VPC endpoint will be created"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for the VPC endpoint"
  type        = list(string)
}

variable "admin_console_role" {
  description = "List of AWS principals (ARNs) allowed to access the OpenSearch collection with admin permissions from the AWS console."
  type        = list(string)
}

variable "use_ssm_for_admin_role" {
  description = "Read admin role ARN from SSM Parameter Store at /pds/infra/iam/roles/pds_registry_admin_role_arn"
  type        = bool
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}
