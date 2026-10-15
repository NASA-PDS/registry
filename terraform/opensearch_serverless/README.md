# PDS Registry — OpenSearch Serverless

Deploys the OpenSearch Serverless collection used as the registry data store.

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
| [aws_opensearchserverless_collection.main](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearchserverless_collection) | resource |
| [aws_opensearchserverless_security_policy.encryption](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearchserverless_security_policy) | resource |
| [aws_opensearchserverless_security_policy.network](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearchserverless_security_policy) | resource |
| [aws_security_group.vpce](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/security_group) | resource |
| [aws_ssm_parameter.collection_arn](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [aws_ssm_parameter.collection_name](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssm_parameter) | resource |
| [aws_vpc_endpoint.opensearch_serverless](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/vpc_endpoint) | resource |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region for resources | `string` | n/a | yes |
| <a name="input_collection_name"></a> [collection\_name](#input\_collection\_name) | Name of the OpenSearch Serverless collection | `string` | n/a | yes |
| <a name="input_common_tags"></a> [common\_tags](#input\_common\_tags) | Common tags to apply to all resources | `map(string)` | n/a | yes |
| <a name="input_standby_replicas"></a> [standby\_replicas](#input\_standby\_replicas) | Enable standby replicas for the collection (ENABLED or DISABLED) | `string` | n/a | yes |
| <a name="input_subnet_ids"></a> [subnet\_ids](#input\_subnet\_ids) | Subnet IDs for the VPC endpoint | `list(string)` | n/a | yes |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC ID where the OpenSearch Serverless VPC endpoint will be created | `string` | n/a | yes |
| <a name="input_component_name"></a> [component\_name](#input\_component\_name) | Component name used for resource naming and tagging | `string` | `"registry"` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_collection_endpoint"></a> [collection\_endpoint](#output\_collection\_endpoint) | The endpoint URL for the OpenSearch Serverless collection |
| <a name="output_dashboard_endpoint"></a> [dashboard\_endpoint](#output\_dashboard\_endpoint) | The OpenSearch Dashboards endpoint URL |
| <a name="output_network_policy_name"></a> [network\_policy\_name](#output\_network\_policy\_name) | The name of the network security policy (update this in AWS Console to change Access Type) |
| <a name="output_network_policy_version"></a> [network\_policy\_version](#output\_network\_policy\_version) | The version of the network security policy |
| <a name="output_security_group_id"></a> [security\_group\_id](#output\_security\_group\_id) | The ID of the security group created for the VPC endpoint |
<!-- END_TF_DOCS -->
