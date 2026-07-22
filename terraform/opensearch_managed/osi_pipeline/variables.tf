variable "aws_region" {
  type        = string
  default     = "us-west-2"
}

variable "pipeline_name" {
  type        = string
  description = "Name of the pipeline (also the cloudwatch log group"
}

variable "pipeline_config_yaml_file" {
  type        = string
  description = "Full path to the pipeline config yaml file."
}

variable "pipeline_role_arn" {
  type        = string
  description = "ARN of the pipeline role."
}

variable "pipeline_max_units" {
  type        = number
  description = "Maximum number of pipeline ingestion units."
}

variable "pipeline_min_units" {
  type        = number
  description = "Minimum number of pipeline ingestion units. Default = 1."
  default     = 1
}

variable "cloudwatch_log_group" {
  type        = string
  description = "Log group for pipeline logging."
}

variable "subnet_ids" {
  type        = string
  description = "Subnet through which to access the pipeline."
}

variable "security_group_ids" {
  type        = string
  description = "Security group associated with the endpoint."
}

variable "vpc_endpoint_management" {
  type        = string
  description = "CUSTOMER or SERVICE - who is managing the vpc endpoint."
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
