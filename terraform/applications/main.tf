locals {
  common_tags = {
    tenant    = "en"
    venue     = var.venue
    component = "registry"
    cicd      = "iac"
    managedby = var.managedby
  }
}

module "registry_sweepers" {
  source = "git::https://github.com/NASA-PDS/registry-sweepers.git//terraform?ref=simplify_terraform"

  venue                    = var.venue
  managedby                = var.managedby
  aws_region               = var.aws_region
  aoss_endpoint            = var.aoss_endpoint
  image_uri                = var.sweepers_image_uri
  mwaa_execution_role_name = var.mwaa_execution_role_name
  nodes                    = var.sweepers_nodes
}

module "credentials_api" {
  source = "./credentials_api"

  aws_region                              = var.aws_region
  aws_profile                             = var.aws_profile
  environment                             = var.environment
  collection_name                         = var.collection_name
  standby_replicas                        = var.standby_replicas
  admin_roles                             = var.admin_roles
  readonly_roles                          = var.readonly_roles
  node_list                               = var.node_list
  node_nucleus_harvest_iam_roles          = var.node_nucleus_harvest_iam_roles
  common_tags                             = local.common_tags
  vpc_id                                  = var.vpc_id
  subnet_ids                              = var.subnet_ids
  public_subnet_ids                       = var.public_subnet_ids
  security_group_ids                      = var.security_group_ids
  lambda_runtime                          = var.lambda_runtime
  lambda_timeout                          = var.lambda_timeout
  lambda_memory_size                      = var.lambda_memory_size
  cognito_allowed_groups                  = var.cognito_allowed_groups
  cognito_user_pool_id                    = var.cognito_user_pool_id
  cognito_identity_pool_id                = var.cognito_identity_pool_id
  api_gateway_name                        = var.api_gateway_name
  api_gateway_stage_name                  = var.api_gateway_stage_name
  aws_s3_bucket_logs_id                   = var.aws_s3_bucket_logs_id
  registry_api_docker_image               = var.registry_api_docker_image
  registry_api_ecs_service_security_group = var.registry_api_ecs_service_security_group
  acm_certificate_arn                     = var.acm_certificate_arn
}
