# PDS Registry — Security

Manages the OpenSearch Serverless data access policy.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.32.1 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_aws"></a> [aws](#provider\_aws) | 6.32.1 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [aws_opensearchserverless_access_policy.data_access](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearchserverless_access_policy) | resource |
| [aws_ssm_parameter.opensearch_admin_role_arn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |
| [aws_ssm_parameter.opensearch_node_limited_writer_role_arns](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_admin_roles"></a> [admin\_roles](#input\_admin\_roles) | List of AWS principals (ARNs) allowed to access the OpenSearch collection with admin permissions. | `list(string)` | n/a | yes |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region for resources | `string` | n/a | yes |
| <a name="input_collection_name"></a> [collection\_name](#input\_collection\_name) | Name of the OpenSearch Serverless collection | `string` | n/a | yes |
| <a name="input_node_list"></a> [node\_list](#input\_node\_list) | List of discipline nodes (e.g., ['geo', 'atm', 'img']). For each node, a read-write access rule will be created. | `list(string)` | n/a | yes |
| <a name="input_readonly_roles"></a> [readonly\_roles](#input\_readonly\_roles) | List of AWS principals (ARNs) allowed to access the OpenSearch collection with readonly permissions. | `list(string)` | n/a | yes |
| <a name="input_node_nucleus_harvest_iam_roles"></a> [node\_nucleus\_harvest\_iam\_roles](#input\_node\_nucleus\_harvest\_iam\_roles) | Map of discipline node names to their IAM role ARNs (e.g., { geo = 'arn:aws:iam::...' }). Keys should match entries in node\_list. | `map(string)` | `{}` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
