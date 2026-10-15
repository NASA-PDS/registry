# PDS Registry — OpenSearch Managed

Deploys a managed OpenSearch domain used as the registry data store.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.0 |

## Providers

| Name | Version |
| ---- | ------- |
| <a name="provider_aws"></a> [aws](#provider\_aws) | ~> 6.0 |

## Modules

No modules.

## Resources

| Name | Type |
| ---- | ---- |
| [aws_opensearch_domain.pds-opensearch-domain](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearch_domain) | resource |
| [aws_opensearch_domain_policy.domain_access_policy](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearch_domain_policy) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.domain_access_policy_document](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_domain_name"></a> [domain\_name](#input\_domain\_name) | Name of the provisioned opensearch domain. | `string` | n/a | yes |
| <a name="input_ebs_volume_gb"></a> [ebs\_volume\_gb](#input\_ebs\_volume\_gb) | The size of the ebs volume per data node, in GB | `number` | n/a | yes |
| <a name="input_policy_json_file"></a> [policy\_json\_file](#input\_policy\_json\_file) | Full path name to access policy json file. | `string` | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | Tag value of venue | `string` | n/a | yes |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | Effective AWS Region | `string` | `"us-west-2"` | no |
| <a name="input_cicd"></a> [cicd](#input\_cicd) | Tag value of CICD deployment method | `string` | `"terraform"` | no |
| <a name="input_component"></a> [component](#input\_component) | Tag value of component | `string` | `"registry"` | no |
| <a name="input_data_node_count"></a> [data\_node\_count](#input\_data\_node\_count) | The number of data nodes. | `number` | `3` | no |
| <a name="input_data_node_instance_type"></a> [data\_node\_instance\_type](#input\_data\_node\_instance\_type) | The instance type for the data nodes. | `string` | `"r6g.xlarge.search"` | no |
| <a name="input_ebs_volume_type"></a> [ebs\_volume\_type](#input\_ebs\_volume\_type) | The EBS volume type | `string` | `"gp3"` | no |
| <a name="input_encryption_at_rest"></a> [encryption\_at\_rest](#input\_encryption\_at\_rest) | Encryption at rest | `bool` | `true` | no |
| <a name="input_managedBy"></a> [managedBy](#input\_managedBy) | Tag value for owner managing the resource (E.g. for PDS Team we have PDS Team Email Distro) | `string` | `"pdsoperator@jpl.nasa.gov"` | no |
| <a name="input_master_node_count"></a> [master\_node\_count](#input\_master\_node\_count) | The number of master nodes. | `number` | `3` | no |
| <a name="input_master_node_instance_type"></a> [master\_node\_instance\_type](#input\_master\_node\_instance\_type) | The instance type for the master nodes. | `string` | `"m6g.large.search"` | no |
| <a name="input_n2n_encryption"></a> [n2n\_encryption](#input\_n2n\_encryption) | Node to node encryption | `bool` | `true` | no |
| <a name="input_tenant"></a> [tenant](#input\_tenant) | Tag value of tenant | `string` | `"en"` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->
