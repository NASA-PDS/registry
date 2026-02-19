# OpenSearch Serverless Collection Module


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

# Data access policy - defines who can access the data
resource "aws_opensearchserverless_access_policy" "data_access" {
  name        = "${var.collection_name}-access"
  type        = "data"
  description = "Data access policy for ${var.collection_name}"

  policy = jsonencode(concat(
    [
      # We consider 3 levels of authorization:
      # - full access across the full collection, for admins
      # - read only across the full collection
      # - write access to specific indexes sharing the same prefix related to a discipline node, e.g. geo-*
      # Authentication access can be granted though Cognito groups or adhoc specific IAM roles.
      {
        Rules = [
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
        "Principal" : var.admin_roles,
        "Description" : "PDS - OpenSearch Admin Access"
      },
      {
        Rules = [
          {
            "Resource" : [
              "collection/${var.collection_name}*"
            ],
            "Permission" : [
              "aoss:DescribeCollectionItems"
            ],
            "ResourceType" : "collection"
          },
          {
            "Resource" : [
              "index/*/*"
            ],
            "Permission" : [
              "aoss:ReadDocument",
              "aoss:DescribeIndex"
            ],
            "ResourceType" : "index"
          }
        ],
        "Principal" : var.readonly_roles,
        "Description" : "PDS - OpenSearch Read-only Access"
      }
    ],
    # Dynamic rules for discipline nodes (e.g., geo, atm, img)
    # Each node gets read-write access to indexes matching {node}-* pattern
    [
      for node in var.node_list : {
        Rules = [
          {
            "Resource" : [
              "collection/${var.collection_name}*"
            ],
            "Permission" : [
              "aoss:DescribeCollectionItems"
            ],
            "ResourceType" : "collection"
          },
          {
            "Resource" : [
              "index/*/${node}-*"
            ],
            "Permission" : [
              "aoss:UpdateIndex",
              "aoss:DescribeIndex",
              "aoss:ReadDocument",
              "aoss:WriteDocument"
            ],
            "ResourceType" : "index"
          }
        ],
        "Principal" : [
          "arn:aws:iam::${var.aws_account_id}:role/pds_${node}_limited_writer"
        ],
        "Description" : "PDS ${upper(node)} - OpenSearch Limited-Write Access"
      }
    ]
  ))
}

# OpenSearch Serverless Collection
resource "aws_opensearchserverless_collection" "main" {
  name        = var.collection_name
  type        = "SEARCH"
  description = "OpenSearch Serverless collection for Registry ${var.environment}"

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
