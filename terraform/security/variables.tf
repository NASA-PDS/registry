variable "aws_region" {
  description = "AWS region for resources"
  type        = string
}

variable "collection_name" {
  description = "Name of the OpenSearch Serverless collection"
  type        = string
}

variable "admin_roles" {
  description = "List of AWS principals (ARNs) allowed to access the OpenSearch collection with admin permissions."
  type        = list(string)
}

variable "readonly_roles" {
  description = "List of AWS principals (ARNs) allowed to access the OpenSearch collection with readonly permissions."
  type        = list(string)
}

variable "node_list" {
  description = "List of discipline nodes (e.g., ['geo', 'atm', 'img']). For each node, a read-write access rule will be created."
  type        = list(string)
}

variable "node_nucleus_harvest_iam_roles" {
  description = "Map of discipline node names to their IAM role ARNs (e.g., { geo = 'arn:aws:iam::...' }). Keys should match entries in node_list."
  type        = map(string)
  default     = {}
}
