variable "aws_region" {
  type        = string
  description = "Effective AWS Region"
  default     = "us-west-2"
}

variable "opensearch_url" {
  type        = string
  description = "Opensearch endpoint URL"
}

variable "template_file_pathname" {
  type        = string
  description = "Full path to the index template file."
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
