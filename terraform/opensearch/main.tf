data "aws_caller_identity" "current" {}

# Load external JSON files
locals {
  access_policies = jsondecode(file("${path.module}/policies/${var.venue}/data.json"))
}

resource "aws_opensearch_domain" "pds-opensearch-domain" {
  domain_name    = "${var.domain_name}"
  engine_version = "OpenSearch_2.17"

  cluster_config {
    instance_type  = "${var.data_node_instance_type}"
    instance_count = ${var.data_node_count} 

    # 3 x m6g.large.search dedicated master nodes
    dedicated_master_enabled = true
    dedicated_master_type    = "${var.master_node_instance_type}"
    dedicated_master_count   = ${var.master_node_count}

    # Multi-AZ is required for 3 dedicated master nodes to ensure HA
    zone_awareness_enabled = true
    zone_awareness_config {
      availability_zone_count = 3
    }
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    # EBS volume size is specified in GB per data node
    volume_size = $var.ebs_volume_gb
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }
}

data "aws_iam_policy_document" "domain_access_policy_document" {
  description = "Data access policies to define access to ${var.domain_name}"

  policy = jsonencode({
    "Version"   = "2012-10-17",
    "Statement" = [
      for statement in local.access_policies.Statememts : {
        Sid         = statement.Sid,
        Effect      = statement.Effect,
        Action      = statement.Action,
        Resource    = [
          for resource in statement.Resource : 
            replace(
              replace(
                replace(
                  resource, 
                  "{account_id}". data.aws_caller_identity.current.account_id
                ),
                "{region}", "${var.region}"
              ),
              "{domain_name}", "${var.domain_name}"
            )
        ],
        Principal   = [for principal in rule.Principal : replace(principal, "{account_id}", data.aws_caller_identity.current.account_id)]
      }
    ]
  })
}

resource "aws_opensearch_domain_policy" "domain_access_policy" {
  domain_name = "${var.domain_name}"
  access_policies = data.aws_iam_policy_document.domain_access_policy_document
}

