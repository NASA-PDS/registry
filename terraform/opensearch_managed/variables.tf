variable "aws_region" {
  type        = string
  description = "Effective AWS Region"
  default     = "us-west-2"
}

variable "policy_json_file" {
  type        = string
  description = "Optional path to access policy JSON file. If provided, uses static policy. If empty, uses dynamic policy generation from admin_roles/readonly_roles/node_list."
  default     = ""
}

variable "domain_name" {
  type        = string
  description = "Name of the provisioned opensearch domain."
  # "domain_name=pds-mcp-registry-prod-mos"
}

variable "data_node_instance_type" {
  type        = string
  description = "The instance type for the data nodes."
  default     = "r6g.xlarge.search"
}

variable "data_node_count" {
  type        = number
  description = "The number of data nodes."
  default     = 3
}

variable "master_node_instance_type" {
  type        = string
  description = "The instance type for the master nodes."
  default     = "m6g.large.search"
}

variable "master_node_count" {
  type        = number
  description = "The number of master nodes."
  default     = 3
}

variable "ebs_volume_gb" {
  type        = number
  description = "The size of the ebs volume per data node, in GB"
  # 2560
}

variable "ebs_volume_type" {
  type        = string
  description = "The EBS volume type"
  default     = "gp3"
}

variable "n2n_encryption" {
  type        = bool
  description = "Node to node encryption"
  default     = true
}

variable "encryption_at_rest" {
  type        = bool
  description = "Encryption at rest"
  default     = true
}

variable "venue" {
  type        = string
  description = "Tag value of venue"
}

variable "tenant" {
  type        = string
  description = "Tag value of tenant"
  default     = "en"
}

variable "component" {
  type        = string
  description = "Tag value of component"
  default     = "registry"
}

variable "cicd" {
  type        = string
  description = "Tag value of CICD deployment method"
  default     = "terraform"
}

variable "managedBy" {
  type        = string
  description = "Tag value for owner managing the resource (E.g. for PDS Team we have PDS Team Email Distro)"
  default     = "pdsoperator@jpl.nasa.gov"
}

# IAM-related variables for dynamic access policy generation

variable "admin_roles" {
  description = "List of AWS principals (ARNs) for admin access to the OpenSearch domain"
  type        = list(string)
  default     = []
}

variable "readonly_roles" {
  description = "List of AWS principals (ARNs) for readonly access to the OpenSearch domain"
  type        = list(string)
  default     = []
}

variable "node_list" {
  description = "List of discipline nodes (e.g., ['geo', 'atm', 'img']). Each node gets write access to its own index pattern."
  type        = list(string)
  default     = []
}

variable "node_nucleus_harvest_iam_roles" {
  description = "Map of discipline node names to their external harvester IAM role ARNs"
  type        = map(string)
  default     = {}
}

variable "component_name" {
  description = "Component name for SSM path construction (e.g., 'registry')"
  type        = string
  default     = "registry"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
