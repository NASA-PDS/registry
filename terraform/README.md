# AWS OpenSearch Serverless Terraform Configuration

This Terraform configuration creates an AWS OpenSearch Serverless collection with configurable backend state management.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- An S3 bucket for Terraform state storage (for remote backend)
- A DynamoDB table for state locking (optional but recommended)

## Setup

### 1. Configure Backend

Create a `backend-config.tfvars` file from the example:

```bash
cp backend-config.tfvars.example backend-config.tfvars
```

Edit `backend-config.tfvars` with your S3 bucket details:

```hcl
bucket         = "your-terraform-state-bucket"
key            = "registry/opensearch/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-lock"
encrypt        = true
```

### 2. Configure Variables

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your desired configuration:

```hcl
aws_region      = "us-east-1"
collection_name = "my-registry-collection"
environment     = "dev"

# Add IAM principals that can access the collection
allowed_principals = [
  "arn:aws:iam::123456789012:user/your-user",
  "arn:aws:iam::123456789012:role/your-role"
]

# For public access
enable_public_access = true

# OR for VPC-only access
enable_public_access = false
allowed_vpcs = ["vpce-1234567890abcdef0"]
```

### 3. Initialize Terraform

```bash
terraform init -backend-config=backend-config.tfvars
```

For local state (not recommended for production):

```bash
terraform init
```

### 4. Plan and Apply

Review the planned changes:

```bash
terraform plan
```

Apply the configuration:

```bash
terraform apply
```

## Configuration Options

### Collection Types

- `SEARCH` - General purpose search and analytics
- `TIMESERIES` - Optimized for time-series data
- `VECTORSEARCH` - Optimized for vector embeddings and similarity search

### Access Control

**Public Access:**
```hcl
enable_public_access = true
allowed_principals = ["arn:aws:iam::123456789012:user/your-user"]
```

**VPC-Only Access:**
```hcl
enable_public_access = false
allowed_vpcs = ["vpce-1234567890abcdef0"]
allowed_principals = ["arn:aws:iam::123456789012:role/your-role"]
```

### Standby Replicas

Enable for high availability (increases cost):

```hcl
standby_replicas = "ENABLED"
```

## Outputs

After applying, Terraform will output:

- `collection_id` - The unique ID of the collection
- `collection_arn` - The ARN of the collection
- `collection_endpoint` - The API endpoint for the collection
- `dashboard_endpoint` - The OpenSearch Dashboards URL
- `collection_name` - The name of the collection
- `collection_type` - The type of the collection

## Accessing the Collection

### Using AWS CLI

```bash
# Get collection details
aws opensearchserverless get-collection --id <collection-id>

# List collections
aws opensearchserverless list-collections
```

### Using the API

Use the `collection_endpoint` output with AWS Signature Version 4 authentication:

```bash
curl -X GET "https://<collection-endpoint>/_cat/indices" \
  --aws-sigv4 "aws:amz:us-east-1:aoss" \
  --user "$AWS_ACCESS_KEY_ID:$AWS_SECRET_ACCESS_KEY"
```

## Cost Considerations

- OpenSearch Serverless charges for:
  - OpenSearch Compute Units (OCUs) - minimum 2 OCUs
  - Storage (per GB-month)
  - Data transfer
- Standby replicas double the OCU cost
- Consider using `standby_replicas = "DISABLED"` for development

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Troubleshooting

### Authentication Issues

Ensure your IAM user/role has the following permissions:
- `aoss:CreateCollection`
- `aoss:CreateSecurityPolicy`
- `aoss:CreateAccessPolicy`
- IAM permissions to create/manage policies

### Access Denied to Collection

Ensure your IAM principal is listed in `allowed_principals` in the variables.

### VPC Endpoint Issues

For VPC-only access, ensure you've created a VPC endpoint for OpenSearch Serverless in your VPC.

## Security Best Practices

1. **Never commit `backend-config.tfvars` or `terraform.tfvars`** - Add them to `.gitignore`
2. Use IAM roles instead of IAM users when possible
3. Enable encryption at rest (enabled by default in this configuration)
4. Use VPC endpoints for production workloads
5. Enable standby replicas for production environments
6. Regularly review and audit access policies
7. Use DynamoDB table for state locking to prevent concurrent modifications

## References

- [AWS OpenSearch Serverless Documentation](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/serverless.html)
- [Terraform AWS Provider - OpenSearch Serverless](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/opensearchserverless_collection)
