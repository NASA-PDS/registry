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
        "Principal" : concat(var.admin_roles, [data.aws_ssm_parameter.opensearch_admin_role_arn.value]),
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
              "aoss:DescribeCollectionItems",
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
        "Principal" : concat(
          [
            data.aws_ssm_parameter.opensearch_node_limited_writer_role_arns[node].value,
            data.aws_ssm_parameter.opensearch_tenant_core_cloudops_role_arns[node].value
          ],
          contains(keys(var.node_nucleus_harvest_iam_roles), node) ? [var.node_nucleus_harvest_iam_roles[node]] : []
        ),
        "Description" : "PDS ${upper(node)} - OpenSearch Limited-Write Access"
      }
    ]
  ))
}
