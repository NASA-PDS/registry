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

  tags = var.common_tags

}

# VPC Endpoint for OpenSearch Serverless
# TODO this end-point in dev would be shared by multiple opensearch service
# we need to check if that is useful and how to make it re-usable
resource "aws_vpc_endpoint" "opensearch_serverless" {
  vpc_id            = var.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.aoss"
  vpc_endpoint_type = "Interface"
  subnet_ids        = var.subnet_ids

  security_group_ids = [aws_security_group.vpce.id]

  private_dns_enabled = true

  tags = var.common_tags
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


# OpenSearch Serverless Collection
resource "aws_opensearchserverless_collection" "main" {
  name        = var.collection_name
  type        = "SEARCH"
  description = "OpenSearch Serverless collection for Registry"

  standby_replicas = var.standby_replicas

  tags = var.common_tags


  depends_on = [
    aws_opensearchserverless_security_policy.encryption,
    aws_opensearchserverless_security_policy.network,
  ]
}
