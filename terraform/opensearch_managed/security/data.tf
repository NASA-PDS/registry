data "aws_caller_identity" "current" {}

# Build list of SSM parameter names to look up for each role type
locals {
  node_limited_writer_ssm_names = {
    for node in var.node_list :
    node => "/pds/cds-infra/iam/roles/pds-node-limited-writer/${node}"
  }
  core_cloudops_ssm_names = {
    for node in var.node_list :
    node => "/pds/cds-infra/iam/roles/pds-core-cloudops/${node}"
  }
}

# Batch lookup of all requested SSM parameters - returns only those that exist
# This gracefully handles missing parameters (they simply won't be in the result)
data "aws_ssm_parameters_by_path" "node_limited_writer_roles" {
  path = "/pds/cds-infra/iam/roles/pds-node-limited-writer"
}

data "aws_ssm_parameters_by_path" "core_cloudops_roles" {
  path = "/pds/cds-infra/iam/roles/pds-core-cloudops"
}

# Transform the batch results into node-keyed maps for easy lookup
locals {
  # Map of node name -> IAM role ARN for node-limited-writer roles
  node_limited_writer_role_map = {
    for i, name in data.aws_ssm_parameters_by_path.node_limited_writer_roles.names :
    element(split("/", name), length(split("/", name)) - 1) => data.aws_ssm_parameters_by_path.node_limited_writer_roles.values[i]
  }

  # Map of node name -> IAM role ARN for core-cloudops roles
  core_cloudops_role_map = {
    for i, name in data.aws_ssm_parameters_by_path.core_cloudops_roles.names :
    element(split("/", name), length(split("/", name)) - 1) => data.aws_ssm_parameters_by_path.core_cloudops_roles.values[i]
  }
}
