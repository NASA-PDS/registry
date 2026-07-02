terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
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
