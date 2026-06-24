terraform {
  backend "s3" {
    bucket = "pds-prod-infra"
    key    = "provisioned_opensearch/provisioned_opensearch.tfstate"
    region = "us-west-2"
  }
}

data "aws_caller_identity" "current" {}

# Load external JSON files
locals {
  access_policies = jsondecode(file("${var.policy_json_file}"))
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
    for_each = local.access_policies

    content {
      sid         = statement.value.Sid
      effect      = statement.value.Effect
      actions     = statement.value.Action
      resources   = [
        for resource in statement.value.Resource : 
          replace(
            replace(
              replace(
                resource, 
                "{account_id}", data.aws_caller_identity.current.account_id
              ),
              "{region}", "${var.aws_region}"
            ),
            "{domain_name}", "${var.domain_name}"
          )
      ]
      principals {
          type        = "AWS"
          identifiers = [ for principal in statement.value.Principal : replace(principal, "{account_id}", data.aws_caller_identity.current.account_id) ]
      }
    }
  }
}

resource "aws_opensearch_domain_policy" "domain_access_policy" {
  domain_name     = "${var.domain_name}"
  access_policies = data.aws_iam_policy_document.domain_access_policy_document.json

  depends_on = [aws_opensearch_domain.pds-opensearch-domain]
}

