data "aws_ssm_parameter" "opensearch_admin_role_arn" {
  name = "/pds/cds-infra/iam/roles/cognito-admin-role-arn"
}

data "aws_ssm_parameter" "opensearch_readonly_role_arn" {
  name = "/pds/cds-infra/iam/roles/cognito-readonly-role-arn"
}

data "aws_ssm_parameter" "lambda_execution_role_arn" {
  name = "/pds/cds-infra/iam/roles/registry/lambda_execution_role_arn"
}

data "aws_ssm_parameter" "registry_api_ecs_task_role_arn" {
  name     = "/pds/cds-infra/iam/roles/registry/ecs_task_role_arn"
}

data "aws_ssm_parameter" "registry_api_ecs_task_execution_role_arn" {
  name     = "/pds/cds-infra/iam/roles/registry/ecs_task_execution_role_arn"
}
