# Root Terraform Configuration
# This file orchestrates the deployment by calling sub-modules

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# OpenSearch Serverless Collection Module
module "opensearch" {
  source = "./modules/opensearch"

  collection_name        = var.collection_name
  environment            = var.environment
  standby_replicas       = var.standby_replicas
  vpc_id                 = var.vpc_id
  subnet_ids             = var.subnet_ids
  admin_console_role     = var.admin_console_role
  use_ssm_for_admin_role = var.use_ssm_for_admin_role
  aws_region             = var.aws_region
  common_tags            = var.common_tags
}

# External IAM Policies Module
module "external_policies" {
  source = "./modules/external_policies"

  collection_name = var.collection_name
  collection_arn  = module.opensearch.collection_arn
  aws_region      = var.aws_region
  account_id      = data.aws_caller_identity.current.account_id
  common_tags     = var.common_tags
}
