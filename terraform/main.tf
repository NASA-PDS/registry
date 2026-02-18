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

# Security group for VPC endpoint (if not provided)
# TODO move it in the infra repository
resource "aws_security_group" "vpce" {
  name        = "${var.collection_name}-vpce-sg"
  description = "Security group for OpenSearch Serverless VPC endpoint"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.collection_name}-vpce-sg"
    }
  )
}

# VPC Endpoint for OpenSearch Serverless
resource "aws_vpc_endpoint" "opensearch_serverless" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.aoss"
  vpc_endpoint_type = "Interface"
  subnet_ids        = var.subnet_ids

  security_group_ids = [aws_security_group.vpce.id]

  private_dns_enabled = true

  tags = merge(
    var.common_tags,
    {
      Name = "${var.collection_name}-vpce"
    }
  )
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
        },
        {
          Resource = [
            "collection/${var.collection_name}"
          ]
          ResourceType = "dashboard"
        }
      ]
      # TODO; this is not authorized to turn this attribute to true from terraform, need to update it manually in the console for now, need to check with AWS if this is expected or if there is a workaround
      AllowFromPublic = false
      SourceVPCEs     = [aws_vpc_endpoint.opensearch_serverless.id]
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

# Data source to read admin role ARN from SSM (created in separate IAM terraform repo)
# Only reads from SSM if enabled via variable (set to true after IAM role is created)
data "aws_ssm_parameter" "admin_role_arn" {
  count = var.use_ssm_for_admin_role ? 1 : 0
  name  = "/pds/infra/iam/roles/pds_cognito_cds_admin_role_arn"
}

# Locals to handle admin roles from either variables or SSM
locals {
  # Get role ARN from SSM if enabled, otherwise empty string
  ssm_admin_role = var.use_ssm_for_admin_role && length(data.aws_ssm_parameter.admin_role_arn) > 0 ? data.aws_ssm_parameter.admin_role_arn[0].value : ""

  # Combine role from SSM with any directly specified roles, remove empty strings
  all_admin_roles = compact(concat(
    var.admin_console_role, # predefined console roles from variables
    local.ssm_admin_role != "" ? [local.ssm_admin_role] : [] # add SSM role used for Cognito users if it exists (and is not empty
  ))

  # Use admin roles if available, otherwise use empty list (allows initial deployment)
  data_access_principals = local.all_admin_roles
}

# Data access policy - defines who can access the data
resource "aws_opensearchserverless_access_policy" "data_access" {
  name        = "${var.collection_name}-access"
  type        = "data"
  description = "Data access policy for ${var.collection_name}"

  policy = jsonencode(concat([
      {
        Rules = [
          # We consider 3 levels of authorization:
          # - full access across the full collection, for admins
          # - read only across the full collection
          # - write access to specific indexes sharing the same prefix related to a discipline node, e.g. geo-*
          # Authentication access can be granted though Cognito groups or adhoc specific IAM roles.
          {
            "Resource" : [
              "collection/${var.collection_name}*"
            ],
            "Permission" : [
              "aoss:*"
            ],
            "ResourceType" : "collection"
          },
          {
            "Resource" : [
              "index/*/*"
            ],
            "Permission" : [
              "aoss:*"
            ],
            "ResourceType" : "index"
          }
        ],
        "Principal" : local.all_admin_roles,
        "Description" : "PDS - OpenSearch Admin Access"
      }
    ],
    # TODO: add read-only access for read-only roles, and write access for specific indexes for discipline nodes
    []
  ))
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
