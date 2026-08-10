terraform {
  backend "s3" {
    bucket = "pds-prod-infra"
    key    = "provisioned_opensearch/provisioned_opensearch.tfstate"
    region = "us-west-2"
  }
}

data "aws_caller_identity" "current" {}

# Access policy generation - supports two modes:
# 1. Static: If policy_json_file is provided, load policy from JSON file
# 2. Dynamic: If policy_json_file is empty, generate policy from admin_roles/readonly_roles/node_list

locals {
  # Determine which mode to use
  use_static_policy = var.policy_json_file != ""

  # Static policy from JSON file (only loaded if policy_json_file is provided)
  # Example policy file: cds-infra-deploy/terraform/opensearch/dev/policies/dev_policies.json
  # try() guards against Terraform's eager file() evaluation when policy_json_file is empty
  static_policy_statements = local.use_static_policy ? jsondecode(try(file(var.policy_json_file), "[]")) : []

  # Dynamic policy generation (three-tier model)
  # Per-node IAM role ARNs are looked up from SSM parameters created by:
  # pds-cds-infra/terraform/iam/roles/outputs.tf

  # Admin policy statements - full access
  admin_statements = length(var.admin_roles) > 0 ? [{
    Sid        = "AdminAccess"
    Effect     = "Allow"
    Principal  = var.admin_roles
    Action     = ["es:*"]
    Resource   = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/*"]
  }] : []

  # Read-only policy statements
  readonly_statements = length(var.readonly_roles) > 0 ? [{
    Sid        = "ReadOnlyAccess"
    Effect     = "Allow"
    Principal  = var.readonly_roles
    Action     = ["es:ESHttpGet", "es:ESHttpHead"]
    Resource   = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/*"]
  }] : []

  # Per-node write access statements (one per discipline node)
  node_statements = [
    for node in var.node_list : {
      Sid       = "NodeAccess_${node}"
      Effect    = "Allow"
      Principal = compact([
        try(data.aws_ssm_parameter.opensearch_node_limited_writer_role_arns[node].value, ""),
        try(data.aws_ssm_parameter.opensearch_tenant_core_cloudops_role_arns[node].value, ""),
        try(var.node_nucleus_harvest_iam_roles[node], "")
      ])
      Action    = ["es:ESHttpGet", "es:ESHttpHead", "es:ESHttpPost", "es:ESHttpPut", "es:ESHttpDelete"]
      Resource  = ["arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.domain_name}/${node}-*"]
    }
  ]

  # Combine dynamic policy statements
  dynamic_policy_statements = concat(local.admin_statements, local.readonly_statements, local.node_statements)

  # Choose which policy to use
  all_policy_statements = local.use_static_policy ? local.static_policy_statements : local.dynamic_policy_statements
}

resource "aws_opensearch_domain" "pds-opensearch-domain" {
  domain_name    = "${var.domain_name}"
  engine_version = "OpenSearch_2.17"

  cluster_config {
    instance_type  = "${var.data_node_instance_type}"
    instance_count = var.data_node_count

    # 3 x m6g.large.search dedicated master nodes
    dedicated_master_enabled = true
    dedicated_master_type    = "${var.master_node_instance_type}"
    dedicated_master_count   = var.master_node_count

    # Multi-AZ is required for 3 dedicated master nodes to ensure HA
    zone_awareness_enabled = true
    zone_awareness_config {
      availability_zone_count = 3
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "${var.ebs_volume_type}"
    # EBS volume size is specified in GB per data node
    volume_size = var.ebs_volume_gb
  }

  encrypt_at_rest {
    enabled = var.encryption_at_rest
  }

  node_to_node_encryption {
    enabled = var.n2n_encryption
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }
}

data "aws_iam_policy_document" "domain_access_policy_document" {
  dynamic "statement" {
    for_each = local.all_policy_statements

    content {
      sid       = statement.value.Sid
      effect    = statement.value.Effect
      actions   = statement.value.Action

      # For static policies, substitute placeholders in resource ARNs
      # For dynamic policies, resources are already fully formed
      resources = local.use_static_policy ? [
        for resource in statement.value.Resource :
          replace(
            replace(
              replace(resource, "{account_id}", data.aws_caller_identity.current.account_id),
              "{region}", var.aws_region
            ),
            "{domain_name}", var.domain_name
          )
      ] : statement.value.Resource

      principals {
        type = "AWS"
        # For static policies, substitute {account_id} in principal ARNs
        identifiers = local.use_static_policy ? [
          for principal in statement.value.Principal :
            replace(principal, "{account_id}", data.aws_caller_identity.current.account_id)
        ] : statement.value.Principal
      }
    }
  }
}

resource "aws_opensearch_domain_policy" "domain_access_policy" {
  domain_name     = "${var.domain_name}"
  access_policies = data.aws_iam_policy_document.domain_access_policy_document.json

  depends_on = [aws_opensearch_domain.pds-opensearch-domain]
}
