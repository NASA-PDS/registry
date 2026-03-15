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

### Post deployment updates

Go to the AWS console, OpenSearch serverless, network policies, select `Network policies > {collection name}-network`

Edit it to change the access to public.



### Initialize the registry

The registry needs a schema to be intialized and for integration test purpose we also want to load some reference data in it. To do so, you can use the registry-loader utility as described in

Most of the needed configuration is pulled from the terraform output but additional environment is required:

```bash
export COGNITO_CLIENT_ID={the cognito client id}
export COGNITO_USER_POOL_ID={the cognito user pool id}
export COGNITO_ADMIN_USERNAME={a valid user name to create the registry(admin user)}
export COGNITO_ADMIN_PASSWORD={their password}
export COGNITO_WRITER_USERNAME={a valid user name to load data in the registry(writer user)}
export COGNITO_WRITER_PASSWORD={their password}
export TEST_DATA_URL=https://github.com/NASA-PDS/registry-ref-data/releases/download/Latest/custom-datasets.tar.gz
export NODE_REGISTRY=geo-registry
export REG_LOADER_IMAGE=nasapds/registry-loader-lite:latest
```

Then set you python environment:

    python3.12 -m venv venv
    source venv/bin/activate
    pip install jinja2 requests


And run the script to initialize the registry:

    python run-init-on-aws.py