variable "region" {
  type        = string
  default     = "us-west-2"
}

variable "domain_name" {
  type        = string
  description = "Name of the provisioned opensearch domain."
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
}

variable "venue" {
  type        = string
  description = "Value of venue as well as the venue tag"
}

variable "product_tag_value" {
  type        = string
  description = "Value of product tag"
  default     = "PDS Registry"
}

variable "tenant_tag_value" {
  type        = string
  description = "Value of tenant tag"
  default     = "en"
}

variable "component_tag_value" {
  type        = string
  description = "Value of component tag"
  default     = "opensearch"
}

variable "cicd_tag_value" {
  type        = string
  description = "Value of cicd tag"
  default     = "terraform"
}

variable "managedBy_tag_value" {
  type        = string
  description = "Value of managedBy tag"
  default     = "pdsoperator@jpl.nasa.gov"
}
