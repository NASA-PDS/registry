# PDS Registry — Applications

Deploys the application-layer infrastructure: credentials API (API Gateway + Lambda) and registry-sweepers (ECS Fargate).

## Technical architecture

```mermaid
flowchart TB
    subgraph clients["External clients"]
        PDS["PDS client\n(needs temporary AWS credentials)"]
        MWAA["MWAA / Airflow\n(scheduled sweeper runs)"]
    end

    subgraph vpc["VPC (private subnets + security groups)"]
        APIGW["API Gateway\nGET /credentials"]
        Lambda["Lambda\npds-registry-get-awskeys-from-cognitojwt"]
        subgraph fargate["ECS Fargate (one task definition per node)"]
            SweeperEN["registry-sweepers — en"]
            SweeperGEO["registry-sweepers — geo"]
        end
    end

    subgraph aws_managed["AWS managed services"]
        Cognito["Cognito\nUser Pool + Identity Pool"]
        AOSS["OpenSearch Serverless\n(AOSS endpoint)"]
        CW_Lambda["CloudWatch Logs\n/aws/lambda/pds-registry-get-awskeys-..."]
        CW_ECS["CloudWatch Logs\n/pds/ecs/pds-registry-sweepers-{node}-task"]
        SSM["SSM Parameter Store\n/pds/cds-infra/iam/roles/..."]
    end

    PDS -->|"GET /credentials + JWT"| APIGW
    APIGW --> Lambda
    Lambda -->|"validate JWT via JWKS URL"| Cognito
    Lambda -->|"assume role → temp credentials"| Cognito
    Lambda -.->|"logs"| CW_Lambda
    Lambda -.->|"reads IAM role ARNs at deploy time"| SSM

    MWAA -->|"RunTask (iam:PassRole)"| SweeperEN
    MWAA -->|"RunTask (iam:PassRole)"| SweeperGEO
    SweeperEN -->|"index / sweep"| AOSS
    SweeperGEO -->|"index / sweep"| AOSS
    SweeperEN -.->|"logs"| CW_ECS
    SweeperGEO -.->|"logs"| CW_ECS
```

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
| ---- | ------- |
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.0 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | ~> 6.32.1 |

## Providers

No providers.

## Modules

| Name | Source | Version |
| ---- | ------ | ------- |
| <a name="module_credentials_api"></a> [credentials\_api](#module\_credentials\_api) | ./credentials_api | n/a |
| <a name="module_registry_sweepers"></a> [registry\_sweepers](#module\_registry\_sweepers) | git::https://github.com/NASA-PDS/registry-sweepers.git//terraform | develop |

## Resources

No resources.

## Inputs

| Name | Description | Type | Default | Required |
| ---- | ----------- | ---- | ------- | :------: |
| <a name="input_aoss_endpoint"></a> [aoss\_endpoint](#input\_aoss\_endpoint) | Registry AOSS endpoint URL | `string` | n/a | yes |
| <a name="input_managedby"></a> [managedby](#input\_managedby) | Person or system responsible for the deployment | `string` | n/a | yes |
| <a name="input_sweepers_image_uri"></a> [sweepers\_image\_uri](#input\_sweepers\_image\_uri) | registry-sweepers Docker image URI | `string` | n/a | yes |
| <a name="input_sweepers_nodes"></a> [sweepers\_nodes](#input\_sweepers\_nodes) | Map of node IDs to ECS resource allocations for registry-sweepers | <pre>map(object({<br/>    cpu             = number<br/>    memory          = number<br/>    additional_args = optional(string)<br/>  }))</pre> | n/a | yes |
| <a name="input_venue"></a> [venue](#input\_venue) | Deployment venue (e.g. pds-en-dev, prod), used in resource tags across all modules | `string` | n/a | yes |
| <a name="input_acm_certificate_arn"></a> [acm\_certificate\_arn](#input\_acm\_certificate\_arn) | ACM Certificate ARN used for HTTPS access to the Registry API load balancer, re-use the certificate of the cloudfront distribution DNS | `string` | `""` | no |
| <a name="input_admin_roles"></a> [admin\_roles](#input\_admin\_roles) | List of AWS principals (ARNs) allowed to access the OpenSearch collection with admin permissions. | `list(string)` | `[]` | no |
| <a name="input_api_gateway_name"></a> [api\_gateway\_name](#input\_api\_gateway\_name) | Name of the API Gateway | `string` | `"pds-registry-api"` | no |
| <a name="input_api_gateway_stage_name"></a> [api\_gateway\_stage\_name](#input\_api\_gateway\_stage\_name) | API Gateway deployment stage name | `string` | `"prod"` | no |
| <a name="input_aws_profile"></a> [aws\_profile](#input\_aws\_profile) | AWS profile to use for authentication | `string` | `""` | no |
| <a name="input_aws_region"></a> [aws\_region](#input\_aws\_region) | AWS region for resources | `string` | `"us-east-1"` | no |
| <a name="input_aws_s3_bucket_logs_id"></a> [aws\_s3\_bucket\_logs\_id](#input\_aws\_s3\_bucket\_logs\_id) | ID of the S3 bucket used for registry-api load balancer access logs | `string` | `""` | no |
| <a name="input_cognito_allowed_groups"></a> [cognito\_allowed\_groups](#input\_cognito\_allowed\_groups) | List of Cognito groups allowed to access the Lambda function | `list(string)` | `[]` | no |
| <a name="input_cognito_identity_pool_id"></a> [cognito\_identity\_pool\_id](#input\_cognito\_identity\_pool\_id) | Cognito Identity Pool ID for Lambda authentication | `string` | `""` | no |
| <a name="input_cognito_user_pool_id"></a> [cognito\_user\_pool\_id](#input\_cognito\_user\_pool\_id) | Cognito User Pool ID for Lambda authentication | `string` | `""` | no |
| <a name="input_collection_name"></a> [collection\_name](#input\_collection\_name) | Name of the OpenSearch Serverless collection | `string` | `"registry-collection"` | no |
| <a name="input_environment"></a> [environment](#input\_environment) | Environment name (dev, staging, prod) | `string` | `"dev"` | no |
| <a name="input_lambda_memory_size"></a> [lambda\_memory\_size](#input\_lambda\_memory\_size) | Lambda function memory size in MB | `number` | `512` | no |
| <a name="input_lambda_runtime"></a> [lambda\_runtime](#input\_lambda\_runtime) | Lambda runtime version | `string` | `"python3.13"` | no |
| <a name="input_lambda_timeout"></a> [lambda\_timeout](#input\_lambda\_timeout) | Lambda function timeout in seconds | `number` | `30` | no |
| <a name="input_mwaa_execution_role_name"></a> [mwaa\_execution\_role\_name](#input\_mwaa\_execution\_role\_name) | Name of the MWAA execution role that needs iam:PassRole to launch ECS tasks | `string` | `""` | no |
| <a name="input_node_list"></a> [node\_list](#input\_node\_list) | List of discipline nodes (e.g., ['geo', 'atm', 'img']). For each node, a read-write access rule will be created for the pattern '{node}-*' with the principal 'arn:aws:iam::{account\_id}:role/pds-registry-{node}-read-write-aoss-role' | `list(string)` | `[]` | no |
| <a name="input_node_nucleus_harvest_iam_roles"></a> [node\_nucleus\_harvest\_iam\_roles](#input\_node\_nucleus\_harvest\_iam\_roles) | Map of discipline node names to their IAM role ARNs (e.g., { geo = 'arn:aws:iam::...' }). Keys should match entries in node\_list. | `map(string)` | `{}` | no |
| <a name="input_public_subnet_ids"></a> [public\_subnet\_ids](#input\_public\_subnet\_ids) | Subnet IDs for the registry API load balancer | `list(string)` | `[]` | no |
| <a name="input_readonly_roles"></a> [readonly\_roles](#input\_readonly\_roles) | List of AWS principals (ARNs) allowed to access the OpenSearch collection with readonly permissions. | `list(string)` | `[]` | no |
| <a name="input_registry_api_docker_image"></a> [registry\_api\_docker\_image](#input\_registry\_api\_docker\_image) | Docker image URI for the registry-api ECS service | `string` | `""` | no |
| <a name="input_registry_api_ecs_service_security_group"></a> [registry\_api\_ecs\_service\_security\_group](#input\_registry\_api\_ecs\_service\_security\_group) | Security group associated ot the ECS Service | `string` | `""` | no |
| <a name="input_security_group_ids"></a> [security\_group\_ids](#input\_security\_group\_ids) | Security group IDs for the VPC endpoint (if not provided, a default security group will be created) | `list(string)` | `[]` | no |
| <a name="input_standby_replicas"></a> [standby\_replicas](#input\_standby\_replicas) | Enable standby replicas for the collection (ENABLED or DISABLED) | `string` | `"DISABLED"` | no |
| <a name="input_subnet_ids"></a> [subnet\_ids](#input\_subnet\_ids) | Subnet IDs for the VPC endpoint (required if create\_vpc\_endpoint is true) and for the Registry API ECS Service | `list(string)` | `[]` | no |
| <a name="input_vpc_id"></a> [vpc\_id](#input\_vpc\_id) | VPC ID where the OpenSearch Serverless VPC endpoint will be created (required if create\_vpc\_endpoint is true) | `string` | `""` | no |

## Outputs

| Name | Description |
| ---- | ----------- |
| <a name="output_api_gateway_endpoint"></a> [api\_gateway\_endpoint](#output\_api\_gateway\_endpoint) | Base URL of the API Gateway |
| <a name="output_api_gateway_id"></a> [api\_gateway\_id](#output\_api\_gateway\_id) | ID of the API Gateway |
| <a name="output_cognito_jwks_url"></a> [cognito\_jwks\_url](#output\_cognito\_jwks\_url) | Cognito JWKS URL used for JWT token validation |
| <a name="output_credentials_endpoint"></a> [credentials\_endpoint](#output\_credentials\_endpoint) | Full URL for the GET /credentials endpoint |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | ARN of the Lambda function |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | Name of the Lambda function |
| <a name="output_lambda_log_group_arn"></a> [lambda\_log\_group\_arn](#output\_lambda\_log\_group\_arn) | ARN of the Lambda CloudWatch Log Group |
| <a name="output_lambda_log_group_name"></a> [lambda\_log\_group\_name](#output\_lambda\_log\_group\_name) | Name of the Lambda CloudWatch Log Group |
| <a name="output_node_list"></a> [node\_list](#output\_node\_list) | List of discipline nodes |
| <a name="output_sweepers_log_group_names"></a> [sweepers\_log\_group\_names](#output\_sweepers\_log\_group\_names) | Map of node name to CloudWatch log group name |
| <a name="output_sweepers_task_definition_arns"></a> [sweepers\_task\_definition\_arns](#output\_sweepers\_task\_definition\_arns) | Map of node name to ECS task definition ARN |
| <a name="output_sweepers_task_role_arn"></a> [sweepers\_task\_role\_arn](#output\_sweepers\_task\_role\_arn) | Sweeper task role ARN needed to update the OpenSearch data access policy |
<!-- END_TF_DOCS -->
