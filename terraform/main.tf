# OpenSearch Serverless Collection

# Encryption policy - required before creating collection
resource "aws_opensearchserverless_security_policy" "encryption" {
  name        = "${var.collection_name}-encryption"
  type        = "encryption"
  description = "Encryption policy for ${var.collection_name}"

  policy = jsonencode({
    Rules = [
      {
        Resource = [
          "collection/${var.collection_name}"
        ]
        ResourceType = "collection"
      }
    ]
    AWSOwnedKey = true
  })
}

# Network policy - defines public/VPC access
resource "aws_opensearchserverless_security_policy" "network" {
  name        = "${var.collection_name}-network"
  type        = "network"
  description = "Network policy for ${var.collection_name}"

  policy = jsonencode([
    {
      Rules = [
        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          ResourceType = "collection"
        }
      ]
      AllowFromPublic = var.enable_public_access
      SourceVPCEs     = var.allowed_vpcs
    }
  ])
}


# User policy for admin users
resource "aws_iam_policy" "opensearch_admin_access" {
  name        = "${var.collection_name}-admin-access"
  description = "IAM policy for OpenSearch Serverless admin access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "aoss:APIAccessAll"
        Resource = aws_opensearchserverless_collection.main.arn
      },
      {
        Effect = "Allow"
        Action = "aoss:DashboardsAccessAll"
        Resource = "arn:aws:aoss:${var.aws_region}:${data.aws_caller_identity.current.account_id}:dashboards/default"
      }
    ]
  })

  tags = var.common_tags
}

# Store IAM policy ARN in SSM Parameter Store
resource "aws_ssm_parameter" "admin_policy_arn" {
  name        = "/pds/registry/iam_policies/admin"
  description = "IAM policy ARN for OpenSearch Serverless admin access"
  type        = "String"
  value       = aws_iam_policy.opensearch_admin_access.arn

  tags = var.common_tags
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}

# Data access policy - defines who can access the data
resource "aws_opensearchserverless_access_policy" "data_access" {
  name        = "${var.collection_name}-access"
  type        = "data"
  description = "Data access policy for ${var.collection_name}"

  policy = jsonencode([
    {
      Rules = [
        # We consider 3 levels of authorization:
        # - full access across the full collection, for admins
        # - read only across the full collection
        # - write access to specific indexes sharing the same prefix related to a discipline node, e.g. geo-*
        # Authentication access can be granted though Cognito groups or adhoc specific IAM roles.
        {
        "Resource": [
          "collection/${var.collection_name}*"
        ],
        "Permission": [
          "aoss:*"
        ],
        "ResourceType": "collection"
      },
      {
        "Resource": [
          "index/*/*"
        ],
        "Permission": [
          "aoss:*"
        ],
        "ResourceType": "index"
      }
    ],
    "Principal": var.admin_roles
    "Description": "PDS - OpenSearch Admin Access"
  },

        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
          ResourceType = "collection"
        },
        {
          Resource = [
            "index/${var.collection_name}/*"
          ]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument",
            "aoss:UpdateIndex",
            "aoss:DeleteIndex"
          ]
          ResourceType = "index"
        }
      ]
      Principal = var.allowed_principals
    }
  ])
}

# OpenSearch Serverless Collection
resource "aws_opensearchserverless_collection" "main" {
  name        = var.collection_name
  type        = var.collection_type
  description = "OpenSearch Serverless collection for ${var.project_name} ${var.environment}"

  standby_replicas = var.standby_replicas

  tags = merge(
    var.common_tags,
    {
      Name        = var.collection_name
      Environment = var.environment
    }
  )

  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_access_policy.data_access
  ]
}
