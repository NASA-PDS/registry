variable "domain_name" {
  description = "Name of the OpenSearch managed domain to attach the access policy to"
  type        = string
}

variable "aws_region" {
  description = "AWS region where the OpenSearch domain is deployed"
  type        = string
}

variable "admin_roles" {
  description = "List of IAM role/user ARNs granted full es:* access to the domain"
  type        = list(string)
  default     = []
}

variable "readonly_roles" {
  description = "List of IAM role/user ARNs granted read-only access (ESHttpGet, ESHttpHead) to the domain"
  type        = list(string)
  default     = []
}

variable "node_list" {
  description = "List of discipline node names (e.g. ['geo', 'atm', 'img']). Each node gets read-write access to its own index prefix (node-*)."
  type        = list(string)
  default     = []
}

variable "node_nucleus_harvest_iam_roles" {
  description = "Map of discipline node names to their Nucleus harvester IAM role ARNs. Keys must match entries in node_list."
  type        = map(string)
  default     = {}
}

variable "common_tags" {
  description = "Tags to apply to all resources in this module"
  type        = map(string)
  default     = {}
}
