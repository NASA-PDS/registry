data "aws_ssm_parameter" "opensearch_admin_role_arn" {
  name = "/pds/cds-infra/iam/roles/cognito-admin-role-arn"
}

data "aws_ssm_parameter" "opensearch_readonly_role_arn" {
  name = "/pds/cds-infra/iam/roles/cognito-readonly-role-arn"
}

data "aws_ssm_parameter" "lambda_execution_role_arn" {
  name = "/pds/cds-infra/iam/roles/registry/lambda_execution_role_arn"
}