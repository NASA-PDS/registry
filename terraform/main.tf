# Root Terraform Configuration
# This file orchestrates the deployment by calling sub-modules

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# OpenSearch Serverless Collection Module
module "opensearch" {
  source = "./opensearch"

  component_name  = "registry"
  collection_name    = var.collection_name
  standby_replicas   = var.standby_replicas
  vpc_id             = var.vpc_id
  subnet_ids         = var.subnet_ids
  admin_roles        = concat(var.admin_roles, [data.aws_ssm_parameter.opensearch_admin_role_arn.value])
  readonly_roles     = [data.aws_ssm_parameter.opensearch_readonly_role_arn.value, data.aws_ssm_parameter.registry_api_ecs_task_role_arn.value]
  node_list          = var.node_list
  aws_region         = var.aws_region
  common_tags        = var.common_tags
}


# Lambda Module
# Creates Lambda function and CloudWatch Log Group
module "lambda" {
  source = "./lambda"

  runtime                    = var.lambda_runtime
  lambda_execution_role_arn  = data.aws_ssm_parameter.lambda_execution_role_arn.value
  timeout                    = var.lambda_timeout
  memory_size                = var.lambda_memory_size
  cognito_allowed_groups     = var.cognito_allowed_groups
  cognito_user_pool_id       = var.cognito_user_pool_id
  cognito_identity_pool_id   = var.cognito_identity_pool_id
  aws_region                 = var.aws_region
  vpc_subnet_ids             = var.subnet_ids
  vpc_security_group_ids     = var.security_group_ids
  common_tags                = var.common_tags

}

# API Gateway Module
# Integrates with Lambda function for /credentials endpoint
module "api_gateway" {
  source = "./api_gateway"

  api_name             = var.api_gateway_name
  api_description      = "API Gateway for PDS Registry credentials service"
  stage_name           = var.api_gateway_stage_name
  lambda_function_name = module.lambda.lambda_function_name
  lambda_function_arn  = module.lambda.lambda_function_arn
  lambda_invoke_arn    = module.lambda.lambda_invoke_arn
  aws_region           = var.aws_region
  common_tags          = var.common_tags
}

# TL: not ready for integration as we have a deadline for the ISRO node creation in dev, step done manuallyt
# module "registry_api" {
#   source = "git::https://github.com/NASA-PDS/registry-api.git//terraform?ref=terraform_for_dev"
#
#   aws_region = var.aws_region
#   sprint_boot_args = "--openSearch.host=${module.opensearch.collection_endpoint} --openSearch.CCSEnabled=true --openSearch.username='' --openSearch.disciplineNodes=${join(",", var.node_list)} --registry.service.version=1.6.0-SNAPSHOT"
#   aws_s3_bucket_logs_id=var.aws_s3_bucket_logs_id
#   registry_api_docker_image=var.registry_api_docker_image
#   ecs_task_role = data.aws_ssm_parameter.registry_api_ecs_task_role_arn
#   ecs_task_execution_role = data.aws_ssm_parameter.registry_api_ecs_task_execution_role_arn
#   aws_fg_vpc = var.vpc_id
#   aws_fg_security_group = var.registry_api_ecs_service_security_group
#   aws_fg_subnets = var.subnet_ids
#   aws_lb_subnets = var.public_subnet_ids
#   aws_acm_certificate_arn = var.acm_certificate_arn
#
#   common_tags = var.common_tags
#
# }
