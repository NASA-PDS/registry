variable "aws_region" {
  type        = string
  default     = "us-west-2"
}

variable "pipeline_name" {
  type        = string
  description = "Name of the pipeline (also the cloudwatch log group"
}

variable "source_opensearch_url" {
  type        = string
  description = "URI of the source opensearch endpoint."
}

variable "source_opensearch_serverless" {
  type        = boolean
  description = "Boolean indicating if source is AOSS. Default is true."
  default     = true
}

variable "source_batch_size" {
  type        = string
  description = "Size of the source batch reads"
  default     = '1000'
}

variable "sink_opensearch_url" {
  type        = string
  description = "URI of the sink opensearch endpoint."
}

variable "sink_opensearch_serverless" {
  type        = boolean
  description = "Boolean indicating if sink is AOSS. Default is false."
  default     = false
}

variable "pipeline_max_units" {
  type        = number
  description = "Maximum number of pipeline ingestion units."
}

variable "pipeline_min_units: {
  type        = number
  description = "Minimum number of pipeline ingestion units. Default = 1."
  default     = 1
}

variable "aws_venue" {
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
