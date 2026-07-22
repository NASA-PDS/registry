# AWS OpenSearch Serverless Terraform Configuration

This Terraform configuration creates a PDS Registry with configurable backend state management.

It is divided into 3 scripts to match the lifecycle and update frequencies of the resources:

- `opensearch_<serverless|managed>` : to create the opensearch server containing the registry data
- `security`: to create or update the opensearch data access policy, as needed
- `applications`: to continuously deploy the upgraded applications (credentials, TODO: sweepers and api)

For development or test deployment we deploy the 3 scripts always.
For production we only deploy `security` and `applications`, as needed.

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
region         = "us-east-1"
dynamodb_table = "terraform-state-lock"
encrypt        = true
```

### 2. Configure Variables

In each script sub-directory (opensearch_*, security, applications)

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your desired configuration


### 3. Initialize Terraform

In each sub-directory (security, opensearch_*, applications), in this order, as needed:

```bash
terraform init -backend-config=../backend-config.tfvars
```

For local state (not recommended for production):

```bash
terraform init  -backend-config=.../backend-config.tfvars
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

The registry needs a schema to be initialized and for integration test purpose we also want to load some reference data in it. To do so, you can use the registry-loader utility as described in

Most of the needed configuration is pulled from the terraform output but additional environment is required:

```bash
export COGNITO_CLIENT_ID={the cognito client id}
export COGNITO_USER_POOL_ID={the cognito user pool id}
export COGNITO_ADMIN_USERNAME={a valid user name to create the registry(admin user)}
export COGNITO_ADMIN_PASSWORD={their password}
export COGNITO_WRITER_USERNAME={a valid user name to load data in the registry(writer user)}
export COGNITO_WRITER_PASSWORD={their password}
export TEST_DATA_URL=https://github.com/NASA-PDS/registry-ref-data/releases/download/Latest/custom-datasets.tar.gz
export NODE_REGISTRY_WITH_REF_DATA=geo-registry
export REG_LOADER_IMAGE=nasapds/registry-loader-lite:latest
```

Then set you python environment:

    python3.12 -m venv venv
    source venv/bin/activate
    pip install jinja2 requests boto3


And run the script to initialize the registry:

    python run-init-on-aws.py

#### Using terragrunt

If the infrastructure was deployed via terragrunt instead of terraform directly, pass the `--terragrunt` flag. The script uses the current working directory by default, so you can either `cd` to the terragrunt directory first or pass it explicitly with `--working-dir`:

    # option 1: cd to the terragrunt directory first
    cd /path/to/terragrunt/working/directory
    python /path/to/registry/terraform/run-init-on-aws.py --terragrunt

    # option 2: pass the directory explicitly
    python run-init-on-aws.py --terragrunt --working-dir /path/to/terragrunt/working/directory
