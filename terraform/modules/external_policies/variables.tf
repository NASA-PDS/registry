variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
}

variable "collection_arn" {
  description = "ARN of the OpenSearch Serverless collection"
  type        = string
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}
