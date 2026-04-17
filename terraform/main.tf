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
  readonly_roles     = [data.aws_ssm_parameter.opensearch_readonly_role_arn.value]
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
