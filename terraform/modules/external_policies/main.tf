# External IAM Policies Module
# This module creates IAM policies that will be attached to roles defined in a separate repository

# IAM policy for admin users
resource "aws_iam_policy" "opensearch_admin_access" {
  name        = "${var.collection_name}-admin-access"
  description = "IAM policy for OpenSearch Serverless admin access to be used by admin users through their Cognito user groups"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "aoss:APIAccessAll"
        Resource = var.collection_arn
      },
      {
        Effect = "Allow"
        Action = "aoss:DashboardsAccessAll"
        Resource = "arn:aws:aoss:${var.aws_region}:${var.account_id}:dashboards/default"
      }
    ]
  })

  tags = var.common_tags
}


resource "aws_iam_policy" "opensearch_api_only_access" {
  name        = "${var.collection_name}-limited-writer-access"
  description = "IAM policy for OpenSearch Serverless writer access, to be used by nodes through their Cognito user groups"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll",
        ]
        Resource = var.collection_arn
      }
    ]
  })

  tags = var.common_tags
}


