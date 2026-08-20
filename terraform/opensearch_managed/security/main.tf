# OpenSearch Managed Security Module
#
# Manages the aws_opensearch_domain_policy for the PDS managed OpenSearch domain.
# Kept separate from the domain module so IAM role changes (node additions, role
# rotations) can be applied independently without re-provisioning the cluster.

locals {
  # Admin policy statement - full es:* access across the entire domain
  admin_statements = length(var.admin_roles) > 0 ? [{
    Sid       = "AdminAccess"
    Effect    = "Allow"
    Principal = var.admin_roles
    Action    = ["es:*"]
    Resource  = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/*"]
  }] : []

  # Read-only policy statement - HTTP GET and HEAD only, domain-wide
  readonly_statements = length(var.readonly_roles) > 0 ? [{
    Sid       = "ReadOnlyAccess"
    Effect    = "Allow"
    Principal = var.readonly_roles
    Action    = ["es:ESHttpGet", "es:ESHttpHead"]
    Resource  = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/*"]
  }] : []

  # Per-node write access - one statement per discipline node, scoped to node-* indexes
  # Principal list is assembled from three sources per node:
  #   1. SSM: pds-node-limited-writer role (set by pds-cds-infra/terraform/iam/roles)
  #   2. SSM: pds-core-cloudops role (set by pds-cds-infra/terraform/iam/roles)
  #   3. Optional: var.node_nucleus_harvest_iam_roles[node] (passed in directly)
  # compact() removes any empty strings (e.g. when a node has no nucleus harvester role)
  node_statements = [
    for node in var.node_list : {
      Sid       = "NodeAccess${title(node)}"
      Effect    = "Allow"
      Principal = compact([
        try(local.node_limited_writer_role_map[node], ""),
        try(local.core_cloudops_role_map[node], ""),
        try(var.node_nucleus_harvest_iam_roles[node], "")
      ])
      Action   = ["es:ESHttpGet", "es:ESHttpHead", "es:ESHttpPost", "es:ESHttpPut", "es:ESHttpDelete"]
      Resource = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/${node}-*"]
    }
  ]

  all_policy_statements = concat(local.admin_statements, local.readonly_statements, local.node_statements)
}

data "aws_iam_policy_document" "domain_access_policy_document" {
  dynamic "statement" {
    for_each = local.all_policy_statements

    content {
      sid        = statement.value.Sid
      effect     = statement.value.Effect
      actions    = statement.value.Action
      resources  = statement.value.Resource

      principals {
        type        = "AWS"
        identifiers = statement.value.Principal
      }
    }
  }
}

resource "aws_opensearch_domain_policy" "domain_access_policy" {
  domain_name     = var.domain_name
  access_policies = data.aws_iam_policy_document.domain_access_policy_document.json
}
