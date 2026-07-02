terraform {
  backend "s3" {
    bucket = "pds-prod-infra"
    key    = "provisioned_opensearch/opensearch_index_templates.tfstate"
    region = "us-west-2"
  }
}

data "aws_caller_identity" "current" {}

# Load external JSON files
locals {
  index_templates = jsondecode(file("${var.template_file_pathname}"))
}

resource "opensearch_composable_index_template" "pds_index_templates" {
  for_each = local.index_templates

  name = each.key
  body = jsonencode({
    index_patterns = each.value.index_pattern
    priority       = each.value.priority
    template = {
      settings = each.value.settings
      aliases = each.value.aliases
    }
  })
}
