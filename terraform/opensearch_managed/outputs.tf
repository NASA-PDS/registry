# Outputs for the Managed OpenSearch module

output "domain_endpoint" {
  description = "The endpoint URL for the OpenSearch domain"
  value       = aws_opensearch_domain.pds-opensearch-domain.endpoint
}

output "domain_arn" {
  description = "The ARN of the OpenSearch domain"
  value       = aws_opensearch_domain.pds-opensearch-domain.arn
}

output "dashboard_endpoint" {
  description = "The OpenSearch Dashboards endpoint URL"
  value       = aws_opensearch_domain.pds-opensearch-domain.dashboard_endpoint
}

output "domain_name" {
  description = "The name of the OpenSearch domain"
  value       = aws_opensearch_domain.pds-opensearch-domain.domain_name
}

# SSM Parameter storage for cross-module consumption

resource "aws_ssm_parameter" "domain_name" {
  count       = var.component_name != "" ? 1 : 0
  name        = "/pds/${var.component_name}/opensearch_managed/domain_name"
  description = "The name of the Managed OpenSearch domain"
  type        = "String"
  value       = aws_opensearch_domain.pds-opensearch-domain.domain_name
  tags        = var.common_tags
}

resource "aws_ssm_parameter" "domain_arn" {
  count       = var.component_name != "" ? 1 : 0
  name        = "/pds/${var.component_name}/opensearch_managed/domain_arn"
  description = "The ARN of the Managed OpenSearch domain"
  type        = "String"
  value       = aws_opensearch_domain.pds-opensearch-domain.arn
  tags        = var.common_tags
}
