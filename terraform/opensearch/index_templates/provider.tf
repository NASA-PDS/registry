# AWS
# ===
#
# Amazon Web Services: the basics.

terraform {
  required_providers {
    opensearch = {
      source  = "opensearch-project/opensearch"
      version = "2.3.2"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      tenant    = var.tenant
      venue     = var.venue
      component = var.component
      managedBy = var.managedBy
      cicd      = var.cicd
    }
  }
}

provider "opensearch" {
  url = "${var.opensearch_url}"
}
