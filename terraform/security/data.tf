data "aws_ssm_parameter" "opensearch_admin_role_arn" {
  name     = "/pds/cds-infra/iam/roles/cognito-admin-role-arn"
}

data "aws_ssm_parameter" "opensearch_node_limited_writer_role_arns" {
  for_each = toset(var.node_list)
  name     = "/pds/cds-infra/iam/roles/pds-node-limited-writer/${each.value}"
}

data "aws_ssm_parameter" "opensearch_tenant_core_cloudops_role_arns" {
  for_each = toset(var.node_list)
  name     = "/pds/cds-infra/iam/roles/pds-core-cloudops/${each.value}"
}
