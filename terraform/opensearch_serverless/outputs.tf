locals {
  module_relative_path = replace(abspath(path.module), "/^.*\\/terraform\\//", "")
  ssm_prefix = "/pds/${var.component_name}/${local.module_relative_path}"
}


resource  "aws_ssm_parameter" "collection_name" {
  name        = "${local.ssm_prefix}/collection_name"
  description = "The name of the OpenSearch Serverless collection"
  type        = "String"
  value       = aws_opensearchserverless_collection.main.name
  tags        = var.common_tags
}

resource "aws_ssm_parameter" "collection_arn" {
  name        = "${local.ssm_prefix}/collection_arn"
  description = "The ARN of the OpenSearch Serverless collection"
  type        = "String"
  value       = aws_opensearchserverless_collection.main.arn
  tags        = var.common_tags
}

output "collection_endpoint" {
  description = "The endpoint URL for the OpenSearch Serverless collection"
  value       = aws_opensearchserverless_collection.main.collection_endpoint
}

output "dashboard_endpoint" {
  description = "The OpenSearch Dashboards endpoint URL"
  value       = aws_opensearchserverless_collection.main.dashboard_endpoint
}


output "security_group_id" {
  description = "The ID of the security group created for the VPC endpoint"
  value       = aws_security_group.vpce.id
}

output "network_policy_name" {
  description = "The name of the network security policy (update this in AWS Console to change Access Type)"
  value       = aws_opensearchserverless_security_policy.network.name
}

output "network_policy_version" {
  description = "The version of the network security policy"
  value       = aws_opensearchserverless_security_policy.network.policy_version
}
